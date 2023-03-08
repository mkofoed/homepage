from django.views.generic import ListView

# Create your views here.
from .models import Post


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "all_posts_list"
