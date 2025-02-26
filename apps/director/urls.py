from django.urls import path
from . import views
from .views import home, general_assistance, course_assistance, create_student
app_name = 'director_app'


urlpatterns = [
    path('home/', home, name='Home'),
    path('general_assistance/', general_assistance, name='General_Assistance'),
    path('course_assistance/', course_assistance, name='Course_Assistance'),
    path('add_student/', create_student, name='Add_Student'),
    path('populate/', views.PopulateView.as_view(), name='populate_db')
]
