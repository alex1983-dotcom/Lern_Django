from django.urls import path, re_path
from .views import BlogPostListView, BlogPostDetailView, BlogPostShareView, BlogPostCommentView, BlogPostSearchView
from .feeds import LatestPostsFeed

app_name = "blog"

urlpatterns = [
    path("", BlogPostListView.as_view(), name="post_list"),
    re_path(r'^tag/(?P<tag_slug>[-\wа-яА-Я]+)/$', BlogPostListView.as_view(), name='post_list_by_tag'),
    path("<int:year>/<int:month>/<int:day>/<slug:post>/", BlogPostDetailView.as_view(), name="post_detail"),
    path("<int:post_id>/share/", BlogPostShareView.as_view(), name="post_share"),
    path("<int:post_id>/comment/", BlogPostCommentView.as_view(), name='post_comment'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', BlogPostSearchView.as_view(), name='post_search'),
]
