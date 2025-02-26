from django.urls import path
from .consumers import DashboardConsumer, FacialRecognitionConsumer

websocket_urlpatterns = [
    path('ws/dashboard/<slug:slug>/', DashboardConsumer.as_asgi()),
    path('ws/face/', FacialRecognitionConsumer.as_asgi()),

]
