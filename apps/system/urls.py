from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'system_app'

urlpatterns = [
    path('', login_required(views.HomeView.as_view()), name='home'),
    path('student-list/', login_required(views.StudentListView.as_view()), name='student_list'),
    path('update-students-data/', login_required(views.update_status_whatsapp_students), name='update_students_data'),
    path('download-students-data/', login_required(views.download_students_data), name='download_students_data'),
    path('send-contact/', views.send_contact, name='send-contact'),
    path('get-school-report-week/', views.get_school_report_week, name='get_school_report_week'),
    path('send-school-report-week/', views.send_school_report_week, name='send_school_report_week'),
    path('send-school-report-month/', views.send_school_report_month, name='send_school_report_month'),

]
