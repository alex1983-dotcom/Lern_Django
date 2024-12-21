from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView, FormView, View
from .models import Post, Comment
import markdown
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.paginator import Paginator
from taggit.models import Tag
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpResponse, Http404
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PostSerializer, CommentSerializer
from django.db.models import Count
import logging
from django.shortcuts import render


logger = logging.getLogger(__name__)


class BlogPostListView(ListView):
    """
    Представление для отображения списка постов блога с поддержкой пагинации и фильтрации по тегам.
    """
    model = Post
    template_name = 'blog/post/list.html'
    context_object_name = 'posts'
    paginate_by = 3  # Пагинация

    def get_queryset(self):
        """
        Возвращает набор данных постов, отфильтрованных по тегу, если он указан.
        """
        try:
            queryset = Post.published.all()
            tag_slug = self.kwargs.get('tag_slug')
            if tag_slug:
                self.tag = get_object_or_404(Tag, slug=tag_slug)
                queryset = queryset.filter(tags__in=[self.tag])
            else:
                self.tag = None
            return queryset
        except Exception as e:
            logger.error(f"Ошибка при получении набора данных: {e}")
            return Post.published.none()

    def get_context_data(self, **kwargs):
        """
        Добавляет дополнительные данные в контекст, включая общее количество постов и посты на текущей странице.
        """
        try:
            context = super().get_context_data(**kwargs)
            paginator = Paginator(self.get_queryset(), self.paginate_by)
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)

            for post in page_obj.object_list:
                post.body = markdown.markdown(post.body)
            context['total_posts'] = Post.published.count()
            context['posts'] = page_obj
            context['tag'] = self.tag
            return context
        except Exception as e:
            logger.error(f"Ошибка при получении контекста данных: {e}")
            return {}

class BlogPostDetailView(DetailView):
    """
    Представление для отображения детальной информации о посте блога.
    """
    model = Post
    template_name = 'blog/post/detail.html'
    context_object_name = 'post'

    def get_object(self):
        """
        Возвращает объект поста, отфильтрованный по дате публикации и слагу.
        """
        try:
            queryset = self.get_queryset()
            filter_kwargs = {
                'slug': self.kwargs['post'],
                'status': Post.Status.PUBLISHED,
                'publish__year': self.kwargs['year'],
                'publish__month': self.kwargs['month'],
                'publish__day': self.kwargs['day']
            }
            return get_object_or_404(queryset, **filter_kwargs)
        except Http404:
            logger.error("Пост не найден")
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении поста: {e}")
            raise

    def get_context_data(self, **kwargs):
        """
        Добавляет дополнительные данные в контекст, включая комментарии и похожие посты.
        """
        try:
            context = super().get_context_data(**kwargs)
            post = context['post']
            context['post'].body = markdown.markdown(post.body)
            context['comments'] = post.comments.filter(active=True)
            context['form'] = CommentForm()
            context['total_posts'] = Post.published.count()

            # Добавляем код для получения похожих постов
            post_tags_ids = post.tags.values_list('id', flat=True)
            similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
            similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
            context['similar_posts'] = similar_posts

            return context
        except Exception as e:
            logger.error(f"Ошибка при получении контекста данных: {e}")
            raise




class BlogPostShareView(FormView):
    """
    Представление для отправки поста блога по электронной почте.
    """
    template_name = 'blog/post/share.html'
    form_class = EmailPostForm

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает POST-запрос и отправляет пост по электронной почте.
        """
        try:
            post = get_object_or_404(Post, id=self.kwargs['post_id'], status=Post.Status.PUBLISHED)
            sent = False

            form = self.get_form()
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

            total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

            response = render(request, self.template_name, {'post': post, 'form': form, 'sent': sent, 'total_posts': total_posts})
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        except Http404:
            return HttpResponse("Страница не найдена", status=404)
        except Exception as e:
            return HttpResponse(f"Ошибка: {e}", status=500)

    def get(self, request, *args, **kwargs):
        """
        Обрабатывает GET-запрос и отображает форму для отправки поста по электронной почте.
        """
        try:
            post = get_object_or_404(Post, id=self.kwargs['post_id'], status=Post.Status.PUBLISHED)
            form = self.get_form()
            total_posts = Post.published.count()  # Подсчитываем количество опубликованных постов

            response = render(request, self.template_name, {'post': post, 'form': form, 'sent': False, 'total_posts': total_posts})
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        except Http404:
            return HttpResponse("Страница не найдена", status=404)
        except Exception as e:
            return HttpResponse(f"Ошибка: {e}", status=500)



class BlogPostCommentView(View):
    """
    Представление для добавления комментария к посту блога.
    """
    def post(self, request, post_id):
        """
        Обрабатывает POST-запрос для добавления комментария.
        """
        try:
            post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
            form = CommentForm(data=request.POST)
            comment = None
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = post
                comment.save()
            total_posts = Post.published.count()
            return render(request, 'blog/post/comment.html', {
                'post': post,
                'form': form,
                'comment': comment,
                'total_posts': total_posts
            })
        except Exception as e:
            logger.error(f"Ошибка при добавлении комментария: {e}")
            return HttpResponse(f"Ошибка при добавлении комментария: {e}", status=500)


class BlogPostSearchView(FormView):
    """
    Представление для поиска постов блога.
    """
    form_class = SearchForm
    template_name = 'blog/post/search.html'

    def get(self, request, *args, **kwargs):
        """
        Обрабатывает GET-запрос для поиска постов.
        """
        form = self.get_form()
        query = request.GET.get('query', '')
        try:
            if query:
                results = Post.published.annotate(
                    similarity=TrigramSimilarity('title', query)
                ).filter(similarity__gt=0.1).order_by('-similarity')
            else:
                results = []
        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {e}")
            results = []
        context = {
            'form': form,
            'query': query,
            'results': results,
            'total_posts': Post.published.count(),
        }
        return self.render_to_response(context)


class PostListView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию


    def get_queryset(self):
        queryset = Post.published.all()
        tag_slug = self.request.query_params.get('tag_slug')
        if tag_slug:
            try:
                tag = Tag.objects.get(slug=tag_slug)
                queryset = queryset.filter(tags__in=[tag])
            except Tag.DoesNotExist:
                raise NotFound('Тег не найден')
        return queryset


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def get_queryset(self):
        return Post.published.all()

    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {
            'slug': self.kwargs['post'],
            'publish__year': self.kwargs['year'],
            'publish__month': self.kwargs['month'],
            'publish__day': self.kwargs['day']
        }
        try:
            obj = get_object_or_404(queryset, **filter_kwargs)
        except Http404:
            raise NotFound('Пост не найден')
        return obj


class PostShareView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        form = EmailPostForm(request.data)
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
                return Response({'status': 'sent'})
            except Exception as e:
                logger.error(f"Ошибка отправки письма: {e}")
                return Response({'error': str(e)}, status=500)
        return Response(form.errors, status=400)


class CommentCreateView(generics.CreateAPIView):
    """
    API представление для создания комментария к посту.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def perform_create(self, serializer):
        """
        Обрабатывает создание комментария и связывает его с постом.
        """
        try:
            post = get_object_or_404(Post, id=self.kwargs['post_id'], status=Post.Status.PUBLISHED)
            serializer.save(post=post)
        except Http404:
            raise NotFound('Пост не найден')
        except Exception as e:
            logger.error(f"Ошибка при создании комментария: {e}")
            raise


class PostSearchView(generics.ListAPIView):
    """
    API представление для поиска постов блога.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def get_queryset(self):
        """
        Возвращает набор данных постов, отфильтрованных по запросу поиска.
        """
        query = self.request.query_params.get('query', None)
        if query:
            try:
                return Post.published.annotate(
                    similarity=TrigramSimilarity('title', query)
                ).filter(similarity__gt=0.1).order_by('-similarity')
            except Exception as e:
                logger.error(f"Ошибка при выполнении поиска: {e}")
                return Post.published.none()
        return Post.published.none()


