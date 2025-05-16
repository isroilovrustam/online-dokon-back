from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.i18n import i18n_patterns

from config import settings

schema_view = get_schema_view(
    openapi.Info(
        title="DRF API",
        default_version='v1',
        description="Django rest api shablon",
        terms_of_service="https://t.me/abruisbot",
        contact=openapi.Contact(email="rustamjonisroilov213@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
)

urlpatterns = [
    # Swagger
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

    path('admin/', admin.site.urls),
    # path('api/v1/', include('apps.urls'))
]

urlpatterns += i18n_patterns(
    path('api/v1/', include('apps.urls'))
)
