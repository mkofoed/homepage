from django.urls import path

from blog.views import PostListView, PostDetailView, PostCreateView, PostDeleteView, PostUpdateView, AdminPostListView

app_name = "blog"
urlpatterns = [
    path("", PostListView.as_view(), name="list"),
    path("create/", PostCreateView.as_view(), name="create"),
    path("admin/", AdminPostListView.as_view(), name="admin_list"),
    path("<slug:slug>/update/", PostUpdateView.as_view(), name="update"),
    path("<slug:slug>/delete/", PostDeleteView.as_view(), name="delete"),
    path("<slug:slug>/", PostDetailView.as_view(), name="detail"),
]
