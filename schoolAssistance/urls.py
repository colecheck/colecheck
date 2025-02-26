"""
URL configuration for schoolAssistance project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib.auth import views as auth_views

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from apps import gameStop
from colecheck_api.views import BlacklistTokenUpdateView, CurrentUserDetail

not_consider_urls = [
    path('gameStop/', include('apps.gameStop.urls')),
]

urlpatterns = not_consider_urls + [
    path('admin/', admin.site.urls),

    path('system/', include('apps.system.urls')),
    path('student/', include('apps.student.urls')),
    path('director/', include('apps.director.urls')),
    path('assistant/', include('apps.assistant.urls')),
    path('teacher/', include('apps.teacher.urls')),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('api/current-user/', CurrentUserDetail.as_view(), name='current_user'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/logout/blacklist/', BlacklistTokenUpdateView().as_view(), name='blacklist'),
    path('api/', include('colecheck_api.urls')),

    path('', include('apps.school.urls')),

    path('<slug:slug>/', include('apps.assistance.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
