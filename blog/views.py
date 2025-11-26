from django.shortcuts import render, get_object_or_404
from .models import Post

def index(request):
    latest_post = Post.objects.order_by('-created_at').first()
    recent_posts = Post.objects.order_by('-created_at')[1:6]
    return render(request, 'blog/index.html', {
        'latest_post': latest_post,
        'recent_posts': recent_posts
    })

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'blog/post_list.html', {'posts': posts})

def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/detail.html', {'post': post})
