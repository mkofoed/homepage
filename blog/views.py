from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from .models import Post


def index(request: HttpRequest) -> HttpResponse:
    """Blog index page with latest and recent posts."""
    latest_post = Post.objects.order_by('-created_at').first()
    recent_posts = Post.objects.order_by('-created_at')[1:6]
    return render(request, 'blog/index.html', {
        'latest_post': latest_post,
        'recent_posts': recent_posts
    })


def post_list(request: HttpRequest) -> HttpResponse:
    """Paginated list of all blog posts."""
    posts = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'blog/partials/post_list_items.html', {'page_obj': page_obj})

    return render(request, 'blog/post_list.html', {'page_obj': page_obj})


def detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Single blog post detail page."""
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/detail.html', {'post': post})
