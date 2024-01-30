import sys

import django
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home/home.html"

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        return context


class AboutView(TemplateView):
    template_name = "home/about.html"

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context["title"] = "About"
        context["django_version"] = django.__version__
        context["python_version"] = sys.version
        return context
