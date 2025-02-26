from django.urls import path
from . import views
app_name = 'gameStop_app'


urlpatterns = [
    path('', views.GameIndexView.as_view(), name='index'),
]
