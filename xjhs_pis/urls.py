from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# THE ULTIMATE STATIC FILE FIX FOR PYINSTALLER
# This guarantees Bootstrap loads no matter what folder the .exe extracts to
if getattr(settings, 'DEBUG', False):
    static_folder = os.path.join(settings.BASE_DIR, 'staticfiles')
    urlpatterns += static(settings.STATIC_URL, document_root=static_folder)