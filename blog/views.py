from django.shortcuts import render, get_object_or_404
from .models import Post
import markdown



def post_list(request):
    posts = Post.published.all()

    for post in posts:
        # Добавим вывод для отладки
        print(f"Post ID: {post.id}, Title: {post.title}, Slug: {post.slug}")
        print(f"Generated URL: {post.get_absolute_url()}")

    transformed_posts = []
    for post in posts:
        transformed_post = Post(
            id=post.id,
            title=post.title,
            body=markdown.markdown(post.body),
            publish=post.publish,
            author=post.author,
            status=post.status
        )
        transformed_posts.append(transformed_post)

    return render(request, 'blog/post/list.html', {'posts': transformed_posts})



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


