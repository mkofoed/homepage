from typing import Any

from django.db.models import QuerySet
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from markdownx.utils import markdownify

# Create your views here.
from .models import Post


class PostListView(ListView):
    model = Post
    context_object_name = "posts"

    def get_queryset(self) -> QuerySet:
        return Post.objects.filter(published=True).order_by("-date_created")


class AdminPostListView(ListView):
    model = Post
    template_name = "blog/admin_post_list.html"
    context_object_name = "posts"
    permission_required = "user.is_staff"

    def get_queryset(self) -> QuerySet:
        return Post.objects.all().order_by("-date_created")


class PostDetailView(DetailView):
    model = Post
    context_object_name = "post"

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["content"] = markdownify(self.object.content)
        return context

    def get(self, request, *args, **kwargs) -> Any:
        post = self.get_object()
        if post.published or self.request.user.is_staff:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404("Post not found.")


class PostCreateView(CreateView):
    model = Post
    fields = ["title", "content", "published", "summary"]
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("blog:list")
    permission_required = "user.is_staff"

    def form_valid(self, form: Any) -> Any:
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(CreateView):
    model = Post
    fields = ["title", "content", "published", "summary"]
    success_url = reverse_lazy("blog:list")
    permission_required = "user.is_staff"


class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy("blog:list")
    permission_required = "user.is_staff"
