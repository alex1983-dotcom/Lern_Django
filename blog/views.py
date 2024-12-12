from django.shortcuts import render, get_object_or_404
from .models import Post
import markdown
from django.core.paginator import Paginator


def post_list(request):
    posts = Post.published.all()

    # Постраничная разбивка с тремя постами на страницу
    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page', 1)
    posts = paginator.page(page_number)

    # Преобразование текста из Markdown в HTML для каждого поста
    for post in posts:
        post.body = markdown.markdown(post.body)  # Преобразование только тела статьи


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


