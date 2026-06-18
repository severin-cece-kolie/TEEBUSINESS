from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Language switcher endpoint (sets language in session/cookie; no content URL change).
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('pages.urls')),
    path('shop/', include('shop.urls')),
    path('cart/', include('cart.urls')),
    path('account/', include('accounts.urls')),
    path('communication/', include('communication.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
