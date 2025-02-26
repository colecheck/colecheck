from django.urls import path

from . import views
from .generate_pdf_qrs import create_qr_pdf_from_students

app_name = 'assistance_app'

urlpatterns = [
    # Director
    path('all_course_assistance_report/', views.AllCourseAssistanceReport.as_view(),
         name='all_course_assistance_report'),

    # Auxiliar
    path('take_entry_assistance/', views.TakeEntranceAssistanceView.as_view(), name='take_entry_assistance'),
    path('check_fotocheck/', views.CheckFotocheckView.as_view(), name='check_fotocheck'),
    path('create_fotocheck/', views.CreateFotocheckView.as_view(), name='create_fotocheck'),
    path('send_create_fotocheck/', views.send_create_fotocheck, name='send_create_fotocheck'),
    path('send_create_qrs/<int:section_id>/<int:grade_id>/', create_qr_pdf_from_students, name='send_create_qrs'),

    # y director
    path('general_assistance_report/', views.GeneralAssistanceReportView.as_view(), name='general_assistance_report'),
    path('daily_assistance_report/', views.DailyAssistanceReportView.as_view(), name='daily_assistance_report'),
    path('settings/', views.DirectorSettings.as_view(), name='settings'),
    path('download_general_assistance/', views.download_general_assistance, name='download_general_assistance'),
    path('download_course_assistance/', views.download_course_assistance, name='download_course_assistance'),

    # Profesor
    path('take_course_assistance/edit/<int:pk>', views.EditAssistanceView.as_view(), name='edit_course_assistance'),
    path('take_course_assistance/', views.TakeAssistanceView.as_view(), name='take_course_assistance'),

    path('course_assistance_report', views.AssistanceReport.as_view(), name='course_assistance_report'),

    path('add_assistance/', views.AddAssistanceView.as_view(), name='add_assistance'),

    # path('register_assistance/', views.register_assistance, name='register_assistance'),
    # path('report_assistance/', views.ReportAssistance.as_view(), name='report_assistance'),
    # path('suggestions/', views.suggestions_view, name='suggestions'),

    path('add_students/', views.AddStudentsView.as_view(), name='add_students'),
    path('add_teachers/', views.AddTeachersView.as_view(), name='add_teachers'),
    path('add_blocks/', views.AddBlocksView.as_view(), name='add_blocks'),
    path('create_new_block/', views.create_new_block, name='create_new_block'),
    path('add_course/', views.AddCourseView.as_view(), name="add_course"),
    path('create_new_course/', views.create_new_course, name='create_new_course'),

    path('import_xlsx/', views.import_xlsx, name='import_xlsx'),
    path('import_teacher_xlsx/', views.import_teacher_xlsx, name='import_teacher_xlsx'),
    path('store_manual_assistances', views.store_manual_course_assistance, name="store_manual_assistances"),

    path('register_entrance_assistance/', views.register_entrance_assistance, name='register_entrance_assistance'),
    path('register_exit_assistance/', views.register_exit_assistance, name='register_exit_assistance'),

    # Segunda asistencia del día (Solo envía Reporte WSP)
    path('register_entrance_two_assistance/', views.register_entrance_two_assistance,
         name='register_entrance_two_assistance'),
    path('register_exit_two_assistance/', views.register_exit_two_assistance, name='register_exit_two_assistance'),

    path('register_course_assistance/', views.register_course_assistance, name='register_course_assistance'),

    path('start_assistance_session/', views.start_assistance_session, name="start_assistance_session"),
    path('end_assistance_session/', views.end_assistance_session, name="end_assistance_session"),

    path('justify_assistance/', views.JustifyAssistanceView.as_view(), name="justify_assistance"),
    path('send_justification/', views.send_justification, name="send_justification"),
    path('justifications/', views.JustificationsView.as_view(), name="justifications"),

    path('change_level_times/', views.change_level_times, name="change_level_times"),

    path('send_test_messages/', views.SendTestMessagesView.as_view(), name="send_test_messages"),
    path('sent_whatsapp_messages/', views.send_test_messages, name="send_whatsapp_messages"),

    path('other_actions/', views.OtherActionsView.as_view(), name='other_actions'),
    path('normalize_course_assistances/', views.normalize_course_assistances, name='normalize_course_assistances'),

]
