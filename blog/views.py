import logging

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Post

logger = logging.getLogger(__name__)


def index(request: HttpRequest) -> HttpResponse:
    """Blog index page with latest and recent posts."""
    published_posts = Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")
    latest_post = published_posts.first()
    recent_posts = published_posts[1:6]
    return render(request, "blog/index.html", {"latest_post": latest_post, "recent_posts": recent_posts})


def post_list(request: HttpRequest) -> HttpResponse:
    """Paginated list of all blog posts."""
    posts = Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if getattr(request, "htmx", False):
        return render(request, "blog/partials/post_list_items.html", {"page_obj": page_obj})

    return render(request, "blog/post_list.html", {"page_obj": page_obj})


def detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Single blog post detail page."""
    post = get_object_or_404(Post, pk=pk, status=Post.Status.PUBLISHED)
    logger.info("Blog post viewed: %s (id=%d)", post.title, pk)
    return render(request, "blog/detail.html", {"post": post})
