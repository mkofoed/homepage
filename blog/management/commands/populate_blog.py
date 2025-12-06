"""
Management command to populate the blog with sample data.
Usage: python manage.py populate_blog
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post


class Command(BaseCommand):
    """Populate blog with sample posts and create admin user if needed."""

    help = "Creates sample blog posts and an admin user for development/demo purposes"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--username",
            default="admin",
            help="Admin username (default: admin)",
        )
        parser.add_argument(
            "--email",
            default="admin@example.com",
            help="Admin email (default: admin@example.com)",
        )
        parser.add_argument(
            "--password",
            default="password123",
            help="Admin password (default: password123)",
        )

    def handle(self, *args, **options) -> None:
        username = options["username"]
        email = options["email"]
        password = options["password"]

        # Create or get admin user
        user = self._get_or_create_admin(username, email, password)

        # Create sample posts
        self._create_sample_posts(user)

        self.stdout.write(self.style.SUCCESS("Blog population complete!"))

    def _get_or_create_admin(self, username: str, email: str, password: str) -> User:
        """Get existing admin or create new one."""
        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating superuser: {username}")
            return User.objects.create_superuser(username, email, password)
        else:
            self.stdout.write(f"Superuser {username} already exists")
            return User.objects.get(username=username)

    def _create_sample_posts(self, user: User) -> None:
        """Create sample blog posts."""
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
                """,
            },
            {
                "title": "The Beauty of Nature",
                "content": """
Sometimes you just need to disconnect and enjoy the view.

![Nature](https://picsum.photos/seed/nature/800/400)

> "Look deep into nature, and then you will understand everything better." - Albert Einstein
                """,
            },
            {
                "title": "Coding Best Practices",
                "content": """
Here are some tips for writing clean code:

1. **DRY**: Don't Repeat Yourself
2. **KISS**: Keep It Simple, Stupid
3. **YAGNI**: You Ain't Gonna Need It

![Coding](https://picsum.photos/seed/code/800/400)
                """,
            },
            {
                "title": "My Travel Adventures",
                "content": """
Last summer I visited some amazing places.

![Travel](https://picsum.photos/seed/travel/800/400)

The food was incredible!
                """,
            },
            {
                "title": "Future of AI",
                "content": """
Artificial Intelligence is changing the world rapidly.

![AI](https://picsum.photos/seed/ai/800/400)

Are we ready for what comes next?
                """,
            },
        ]

        for i, post_data in enumerate(sample_posts):
            if not Post.objects.filter(title=post_data["title"]).exists():
                post = Post.objects.create(
                    title=post_data["title"],
                    content=post_data["content"].strip(),
                    author=user,
                )
                # Set created_at manually for staggered dates
                post.created_at = timezone.now() - timedelta(days=i)
                post.save(update_fields=["created_at"])
                self.stdout.write(f"Created post: {post.title}")
            else:
                self.stdout.write(f"Post already exists: {post_data['title']}")
