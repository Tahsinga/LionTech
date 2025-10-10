from django import template

register = template.Library()

@register.filter(name='is_meaningful')
def is_meaningful(value):
    """Return True if the value is not empty and not a variant of 'NA'.

    Treats None, empty strings, and common NA variants (case-insensitive)
    as not meaningful.
    """
    if value is None:
        return False
    try:
        s = str(value).strip()
    except Exception:
        return False
    if s == '':
        return False
    low = s.lower()
    # Common NA-like / placeholder values
    na_variants = {'na', 'n/a', 'none', 'null', '-', 'n.a.', 'n.a', 'n/a.', 'n a', 'n.a..', 'unknown', 'n/a (not applicable)', 'n/a (na)'}
    if low in na_variants:
        return False
    return True


@register.filter(name='to_int')
def to_int(value, default=0):
    """Convert value to int for template comparisons. Returns `default` on failure."""
    try:
        return int(value)
    except Exception:
        try:
            # handle float-like strings
            return int(float(str(value)))
        except Exception:
            return default
