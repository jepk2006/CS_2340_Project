"""
Custom template tags for form styling.
"""
from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Add CSS class to a form field widget.
    Usage: {{ form.field|add_class:"css-class-name" }}
    """
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field


@register.filter(name='add_attrs')
def add_attrs(field, attrs_string):
    """
    Add multiple attributes to a form field widget.
    Usage: {{ form.field|add_attrs:"class:css-class,placeholder:Enter text" }}
    """
    if not hasattr(field, 'as_widget'):
        return field
    
    attrs = {}
    for attr_pair in attrs_string.split(','):
        if ':' in attr_pair:
            key, value = attr_pair.split(':', 1)
            attrs[key.strip()] = value.strip()
    
    return field.as_widget(attrs=attrs)

