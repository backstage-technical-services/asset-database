from django.conf import settings


def environment(request):
    return {'is_development': settings.IS_DEVELOPMENT}