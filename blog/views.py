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
from django.contrib.postgres.search import SearchVector


# Представления для HTML-страниц
class BlogPostListView(ListView):
    model = Post
    template_name = 'blog/post/list.html'
    context_object_name = 'posts'
    paginate_by = 3  # Пагинация

    def get_queryset(self):
        queryset = Post.published.all()
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[tag])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        for post in page_obj.object_list:
            post.body = markdown.markdown(post.body)
        context['total_posts'] = Post.published.count()
        context['posts'] = page_obj
        return context

class BlogPostDetailView(DetailView):
    model = Post
    template_name = 'blog/post/detail.html'
    context_object_name = 'post'

    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {
            'slug': self.kwargs['post'],
            'status': Post.Status.PUBLISHED,
            'publish__year': self.kwargs['year'],
            'publish__month': self.kwargs['month'],
            'publish__day': self.kwargs['day']
        }
        return get_object_or_404(queryset, **filter_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'].body = markdown.markdown(context['post'].body)
        context['comments'] = context['post'].comments.filter(active=True)
        context['form'] = CommentForm()
        context['total_posts'] = Post.published.count()
        return context

class BlogPostShareView(FormView):
    template_name = 'blog/post/share.html'
    form_class = EmailPostForm

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'], status=Post.Status.PUBLISHED)
        cd = form.cleaned_data
        post_url = self.request.build_absolute_uri(post.get_absolute_url())
        subject = f"{cd['name']} рекомендует прочитать \"{post.title}\""
        message = f"Прочитать \"{post.title}\" можно по ссылке: {post_url}\n\n" \
                  f"Комментарии от {cd['name']} ({cd['your_email']}): {cd['comments']}"
        email = EmailMessage(subject, message, 'Engineered Thoughts <tiresservice777@yandex.by>', [cd['to_whom']])
        email.content_subtype = 'plain'
        email.charset = 'UTF-8'
        try:
            email.send()
            return self.render_to_response(self.get_context_data(sent=True))
        except Exception as e:
            return HttpResponse(f"Ошибка отправки письма: {e}")

class BlogPostCommentView(View):
    def post(self, request, post_id):
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


class BlogPostSearchView(FormView):
    template_name = 'blog/post/search.html'
    form_class = SearchForm

    def form_valid(self, form):
        query = form.cleaned_data['query']
        results = Post.published.annotate(
            similarity=TrigramSimilarity('title', query)
        ).filter(similarity__gt=0.05).order_by('-similarity')
        print(f"Query: {query}, Results count: {results.count()}")  # Отладочный вывод

        total_posts = Post.published.count()

        context = self.get_context_data(form=form, query=query, results=results, total_posts=total_posts)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Дополнительная логика, если необходимо
        return context

    # def form_invalid(self, form):
    #     context = self.get_context_data(form=form, query='', results=Post.published.none())
    #     return self.render_to_response(context)


# Представления для API с использованием токенов
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
                return Response({'error': str(e)}, status=500)
        return Response(form.errors, status=400)

class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'], status=Post.Status.PUBLISHED)
        serializer.save(post=post)

class PostSearchView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]  # Требует аутентификацию

    def get_queryset(self):
        query = self.request.query_params.get('query', None)
        if query:
            return Post.published.annotate(
                similarity=TrigramSimilarity('title', query)
            ).filter(similarity__gt=0.1).order_by('-similarity')
        return Post.published.none()


from django.shortcuts import render
from django.views import View
from .models import Post

class SimpleSearchView(View):
    def get(self, request):
        query = request.GET.get('query', '')
        results = Post.published.filter(title__icontains=query) if query else []
        return render(request, 'blog/simple_search.html', {'query': query, 'results': results})
