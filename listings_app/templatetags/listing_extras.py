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


@register.filter
def in_favorites(listing_id, favorite_ids):
    """Returns True if listing_id is in the favorite_ids collection.

    Usage: {{ listing.pk|in_favorites:favorite_ids }}
    """
    if not favorite_ids:
        return False
    return listing_id in favorite_ids
