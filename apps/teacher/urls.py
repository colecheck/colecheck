from django.urls import path
from . import views

from .views import home, receive_data_home

app_name = 'teacher_app'

urlpatterns = [
    path('home/', home, name='Home'),
    #path('take_course_assistance/', take_course_assistance, name='Take_Course_Assistance'),
    #path('check_course_assistance/', check_course_assistance, name='Check_Course_Assistance'),
    path('receive-data-home', receive_data_home, name='receive_data_home'),

]
