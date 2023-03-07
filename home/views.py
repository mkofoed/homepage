from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home/home.html"

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        return context
