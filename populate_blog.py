import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Post

def create_data():
    # 1. Create Superuser
    username = "admin"
    email = "admin@example.com"
    password = "password123"
    
    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser: {username}")
        user = User.objects.create_superuser(username, email, password)
    else:
        print(f"Superuser {username} already exists")
        user = User.objects.get(username=username)

    # 2. Create Example Posts
    print("Creating example posts...")
    
    sample_posts = [
        {
            "title": "Getting Started with Django and Docker",
            "content": """
# Introduction

Django and Docker are a match made in heaven. In this post, we'll explore how to set them up.

![Docker and Django](https://picsum.photos/seed/django/800/400)

## Why Docker?

Docker allows you to package your application with all its dependencies...

```python
def hello_world():
    print("Hello from Docker!")
```
            """
        },
        {
            "title": "The Beauty of Nature",
            "content": """
Sometimes you just need to disconnect and enjoy the view.

![Nature](https://picsum.photos/seed/nature/800/400)

> "Look deep into nature, and then you will understand everything better." - Albert Einstein
            """
        },
        {
            "title": "Coding Best Practices",
            "content": """
Here are some tips for writing clean code:

1. **DRY**: Don't Repeat Yourself
2. **KISS**: Keep It Simple, Stupid
3. **YAGNI**: You Ain't Gonna Need It

![Coding](https://picsum.photos/seed/code/800/400)
            """
        },
        {
            "title": "My Travel Adventures",
            "content": """
Last summer I visited some amazing places.

![Travel](https://picsum.photos/seed/travel/800/400)

The food was incredible!
            """
        },
        {
            "title": "Future of AI",
            "content": """
Artificial Intelligence is changing the world rapidly.

![AI](https://picsum.photos/seed/ai/800/400)

Are we ready for what comes next?
            """
        }
    ]

    for i, post_data in enumerate(sample_posts):
        if not Post.objects.filter(title=post_data["title"]).exists():
            post = Post.objects.create(
                title=post_data["title"],
                content=post_data["content"].strip(),
                author=user,
                created_at=timezone.now() - timedelta(days=i)
            )
            # Hack to set created_at manually (since auto_now_add overrides it on create)
            post.created_at = timezone.now() - timedelta(days=i)
            post.save()
            print(f"Created post: {post.title}")
        else:
            print(f"Post already exists: {post_data['title']}")

if __name__ == "__main__":
    create_data()
