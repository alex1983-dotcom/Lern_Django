from django.shortcuts import render, get_object_or_404
from .models import Post
import markdown
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import EmailPostForm, CommentForm, SearchForm
from django.http import HttpResponse, Http404
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Count


def post_list(request, tag_slug=None):
    """
    Представление для отображения списка постов.
    """
    try:
        posts = Post.published.all()
        tag = None
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            posts = posts.filter(tags__in=[tag])
        # Постраничная разбивка с тремя постами на страницу
        paginator = Paginator(posts, 3)
        page_number = request.GET.get('page', 1)
        try:
            posts = paginator.page(page_number)
        except PageNotAnInteger:
            # Если page_number не целое число, то выдать первую страницу
            posts = paginator.page(1)
        except EmptyPage:
            # Если page_number находится вне диапазона, то выдать последнюю страницу результатов
            posts = paginator.page(paginator.num_pages)

        # Преобразование текста из Markdown в HTML для каждого поста
        for post in posts:
            post.body = markdown.markdown(post.body)  # Преобразование только тела статьи

        total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

        response = render(request, 'blog/post/list.html', {
            'posts': posts,
            'tag': tag,
            'total_posts': total_posts
        })
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except Http404:
        return HttpResponse("Страница не найдена", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка: {e}", status=500)

def post_detail(request, year, month, day, post):
    """
    Представление для отображения деталей поста.
    """
    try:
        post = get_object_or_404(Post,
                                 slug=post,
                                 status=Post.Status.PUBLISHED,
                                 publish__year=year,
                                 publish__month=month,
                                 publish__day=day)
        # Список активных комментариев к этому посту
        comments = post.comments.filter(active=True)
        # Форма для комментирования пользователями
        form = CommentForm()

        # Список схожих постов
        post_tags_ids = post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_ids) \
            .exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
                            .order_by('-same_tags', '-publish')[:4]

        # Преобразование текста из Markdown в HTML
        post.body = markdown.markdown(post.body)

        total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

        response = render(request,
                          'blog/post/detail.html',
                          {'post': post,
                           'comments': comments,
                           'form': form,
                           'total_posts': total_posts,
                           'similar_posts': similar_posts})
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except Http404:
        return HttpResponse("Страница не найдена", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка: {e}", status=500)

def post_share(request, post_id):
    """
    Представление для отправки поста по электронной почте.
    """
    try:
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        sent = False

        if request.method == 'POST':
            form = EmailPostForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                post_url = request.build_absolute_uri(post.get_absolute_url())
                subject = f"{cd['name']} рекомендует прочитать \"{post.title}\""
                message = f"Прочитать \"{post.title}\" можно по ссылке: {post_url}\n\n" \
                          f"Комментарии от {cd['name']} ({cd['your_email']}): {cd['comments']}"
                email = EmailMessage(subject, message, 'Engineered Thoughts <tiresservice777@yandex.by>', [cd['to_whom']])
                email.content_subtype = 'plain'
                email.charset = 'UTF-8'
                try:
                    email.send()
                    sent = True
                except Exception as e:
                    return HttpResponse(f"Ошибка отправки письма: {e}")

        else:
            form = EmailPostForm()

        total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

        response = render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent, 'total_posts': total_posts})
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except Http404:
        return HttpResponse("Страница не найдена", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка: {e}", status=500)

@require_POST
def post_comment(request, post_id):
    """
    Представление для добавления комментария к посту.
    """
    try:
        post = get_object_or_404(Post,
                                  id=post_id,
                                  status=Post.Status.PUBLISHED)
        comment = None
        # Комментарий был отправлен
        form = CommentForm(data=request.POST)
        if form.is_valid():
            # создать объект класса Comment, не сохраняя его в базе данных
            comment = form.save(commit=False)
            # Назначить пост комментарию
            comment.post = post
            # Сохранить комментарий  в базе данных
            comment.save()

        total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

        response = render(request, 'blog/post/comment.html',
                          {'post': post,
                           'form': form,
                           'comment': comment,
                           'total_posts': total_posts})
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except Http404:
        return HttpResponse("Страница не найдена", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка: {e}", status=500)

def post_search(request):
    """
    Представление для поиска постов.
    """
    try:
        form = SearchForm()
        query = None
        results = []

        if 'query' in request.GET:
            form = SearchForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data['query']
                results = Post.published.annotate(
                    similarity=TrigramSimilarity('title', query)
                ).filter(similarity__gt=0.1).order_by('-similarity')

        total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

        response = render(request,
                          'blog/post/search.html',
                          {'form': form,
                           'query': query,
                           'results': results,
                           'total_posts': total_posts})
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except Exception as e:
        return HttpResponse(f"Ошибка: {e}", status=500)
