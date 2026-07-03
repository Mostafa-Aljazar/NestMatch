from django import template

register = template.Library()


@register.filter
def bool_attr(listing, field_name):
    """Returns 'checked' if listing.<field_name> is truthy, else ''.

    Usage: <input type="checkbox" name="no_smoking" {{ listing|bool_attr:'no_smoking' }}>
    """
    if listing is None:
        return ''
    return 'checked' if getattr(listing, field_name, False) else ''
