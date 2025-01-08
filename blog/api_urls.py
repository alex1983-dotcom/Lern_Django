from django.urls import path
from .views import PostListView, PostDetailView, PostShareView, CommentCreateView, PostSearchView

app_name = "api"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post_list"),
    path("posts/<int:year>/<int:month>/<int:day>/<slug:post>/", PostDetailView.as_view(), name="post_detail"),
    path("posts/<int:post_id>/share/", PostShareView.as_view(), name="post_share"),
    path("posts/<int:post_id>/comment/", CommentCreateView.as_view(), name="post_comment"),
    path('posts/search/', PostSearchView.as_view(), name='post_search'),
]
