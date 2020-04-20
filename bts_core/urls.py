from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import include, path
from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from . import settings


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [
    path('', include('bts_asset_db.urls')),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('accounts/', include('django.contrib.auth.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('debug', include(debug_toolbar.urls))] + urlpatterns

# urlpatterns = [
#     url(r'^', include('bts_asset_db.urls')),
#     url(r'^api/', include(router.urls)),
#     url(r'^admin/', admin.site.urls),
#     url(r'^accounts/', include('django.contrib.auth.urls'))
