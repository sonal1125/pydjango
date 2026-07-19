# myapp/templatetags/safe_image.py
from django import template
from django.templatetags.static import static

register = template.Library()

@register.filter
def safe_image_url(image_field):
    """
    Returns the image URL if available, else returns the default image URL.
    """
    if image_field and getattr(image_field, 'name', None):
        try:
            return image_field.url
        except ValueError:
            pass
    return static('images/default.jpg')
