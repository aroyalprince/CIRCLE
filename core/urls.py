"""
URL configuration for core project.

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
from social.views import  login_page, dashboard_page, signup_page, chat_page, update_profile, index_page
from django.conf import settings
from django.conf.urls.static import static
from social import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # The API Routes (Backend)
    path('api/', include('social.urls')),

    # The Frontend Routes (UI)
    path('', index_page, name='home'), 
    path('signup/', signup_page, name='signup'),         # Root URL -> Login Page
    path('login/', login_page, name='login'),      # /login -> Login Page
    path('dashboard/', dashboard_page, name='dashboard'),
    path('random-video/', views.random_video_page),
    path('chat/<int:squad_id>/', chat_page, name='chat'), 
    path('api/', include('social.urls')),
    path('api/profile/update/', update_profile, name='update_profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)