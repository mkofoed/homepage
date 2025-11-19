from django.shortcuts import render, get_object_or_404
from .models import Post

def index(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'blog/index.html', {'posts': posts})

def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/detail.html', {'post': post})
