from django import template
register = template.Library()

@register.filter
def has_import_permission(user):
    return user.is_staff and user.has_perm('bts_asset_db.add_pattest')