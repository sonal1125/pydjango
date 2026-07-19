"""
URL configuration for pydjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.http import HttpResponse
from . import settings

##def home(requests):
##    return HttpResponse('<h1>hello world</h1>')

urlpatterns = [
##    path("", home),
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # newly added for user account login and signup. You can choose a different URL path, but using accounts/ is a standard practice and requires less customization later
    path('', include('frontend.urls')),   
    path('cart/', include('cart.urls')), 
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)#for static files css, js, image

#for uploading images
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
