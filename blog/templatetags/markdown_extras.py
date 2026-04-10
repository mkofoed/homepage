import markdown as md
import nh3
from django import template
from django.utils.encoding import force_str
from django.utils.safestring import SafeString, mark_safe

register = template.Library()

ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "pre", "code", "em", "strong",
    "ul", "ol", "li", "blockquote", "hr", "br", "img",
    "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "code": {"class"},  # for syntax highlighting
}


@register.filter(name="markdown")
def markdown_filter(value: str) -> SafeString:
    """Convert markdown to sanitized HTML."""
    html = md.markdown(
        force_str(value),
        extensions=["markdown.extensions.fenced_code", "markdown.extensions.tables"],
    )
    clean_html = nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return mark_safe(clean_html)
