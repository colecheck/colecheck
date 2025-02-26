from django.urls import path
from . import views

app_name = 'school_app'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),

    path('get_levels/', views.get_levels, name='get_levels'),
    path('get_grades/', views.get_grades, name='get_grades'),
    path('get_sections/', views.get_sections, name='get_sections'),
    path('bookstore/', views.generate_duplicates, name='generate_duplicates'),

    path('<slug:slug>/', views.SchoolHomeView.as_view(), name='school_home'),

]
