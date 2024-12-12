from django.shortcuts import render, get_object_or_404
from .models import Post
import markdown


def post_list(request):
    posts = Post.published.all()

    # Преобразование текста из Markdown в HTML для каждого поста
    for post in posts:
        post.body = markdown.markdown(post.body)  # Преобразование только тела статьи

    # Вывод для отладки
    for post in posts:
        print(f"Post ID: {post.id}, Title: {post.title}, Slug: {post.slug}")
        print(f"Generated URL: {post.get_absolute_url()}")

    return render(request, 'blog/post/list.html', {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status=Post.Status.PUBLISHED,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)


    # Преобразование текста из Markdown в HTML
    post.body = markdown.markdown(post.body)

    return render(request,
                  'blog/post/detail.html',
                  {'post': post})


