from django.urls import path
from . import views
from .views import home, assistance, schedule

# from .views_PDF import print_qr_pdf

app_name = 'student_app'


urlpatterns = [
    path('generate_qr/', views.GenerateQrView.as_view(), name='generate_qr'),

    # path('print_qr_pdf/<int:id_student>/<int:id_classroom>/', print_qr_pdf, name='print_qr_pdf'),


    path('home/', home, name='Home'),
    path('assistance/', assistance, name='Student_Assistance'),
    path('schedule/', schedule, name='Student_Schedule'),

]
