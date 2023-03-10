from typing import Any

from django.db import models
from django.utils.text import slugify
from markdownx.models import MarkdownxField


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = MarkdownxField()
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    published = models.BooleanField(default=False)
    summary = models.CharField(max_length=200, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
