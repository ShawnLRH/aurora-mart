from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def highlight(text, search):
    """
    Highlight search terms in text with a yellow background.
    Usage: {{ product.product_name|highlight:query }}
    """
    if not search or not text:
        return text
    
    # Escape HTML special characters in search term
    search = str(search)
    
    # Case-insensitive replacement with highlight
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<span class="highlight">{m.group(0)}</span>',
        str(text)
    )
    
    return mark_safe(highlighted)
