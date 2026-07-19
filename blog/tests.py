from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post


class PublicPostViewTests(TestCase):
    def setUp(self) -> None:
        author = User.objects.create_user("author")
        self.published = Post.objects.create(
            author=author,
            title="Published",
            content="Visible",
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            author=author,
            title="Draft",
            content="Private",
            status=Post.Status.DRAFT,
        )

    def test_public_lists_exclude_drafts(self) -> None:
        for url_name in ("blog_index", "blog_list"):
            response = self.client.get(reverse(url_name))

            self.assertContains(response, self.published.title)
            self.assertNotContains(response, self.draft.title)

    def test_draft_detail_returns_not_found(self) -> None:
        response = self.client.get(reverse("blog_detail", args=[self.draft.pk]))

        self.assertEqual(response.status_code, 404)
