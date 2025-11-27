from django.shortcuts import render, get_object_or_404
from .models import Post

def index(request):
    latest_post = Post.objects.order_by('-created_at').first()
    recent_posts = Post.objects.order_by('-created_at')[1:6]
    return render(request, 'blog/index.html', {
        'latest_post': latest_post,
        'recent_posts': recent_posts
    })

from django.core.paginator import Paginator

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'blog/partials/post_list_items.html', {'page_obj': page_obj})

    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/detail.html', {'post': post})
