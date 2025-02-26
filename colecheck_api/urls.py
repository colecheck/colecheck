from django.urls import path, re_path
from .views import (
    SchoolDetail,
    StudentList,
    TeacherList,
    TeacherCoursesList,
    GeneralAssistanceDetailsList,
    GeneralAssistancesList,
    CourseStudentsList,
    LevelList,
    GradeList,
    SectionList,
    RegisterEntranceGeneralAssistance,
    RegisterExitGeneralAssistance,
    RegisterCourseAssistance,
    ChangeLevelTimes,
    login,
    register_assistance, receive_data, get_info_school, get_students_info
)

app_name = 'api'
urlpatterns = [
    # Obtiene los estudiantes de un colegio
    path('<slug:school_slug>/', SchoolDetail.as_view() , name='school_detail'),
    
    # Obtiene los estudiantes de un colegio
    path('<slug:school_slug>/students/', StudentList.as_view(), name='students_list'),
    # Obtiene los profesortes de un colegio
    path('<slug:school_slug>/teachers/', TeacherList.as_view(), name='teacher_list'),
    # Obtiene los cursos de un profesor
    path('<slug:school_slug>/teacher-courses/<int:teacher_id>/', TeacherCoursesList.as_view() , name='teacher_courses_list'),
    # Obtiene las asistencias generales de un colegio
    path('<slug:school_slug>/general-assistances/', GeneralAssistancesList.as_view(), name='general_assistance_list'),
    # Obtiene los detalles de asistencia general de una fecha
    path('<slug:school_slug>/general-assistances/details/<str:date>/', GeneralAssistanceDetailsList.as_view(), name='gen_assist_det_list'),
    # Obtiene los estudiantes de un curso
    path('<slug:school_slug>/course-students/<int:course_id>/', CourseStudentsList.as_view(), name='course_students_list'),

    path('<slug:school_slug>/levels/', LevelList.as_view(), name='level_list'),
    path('<slug:school_slug>/level/<int:level_id>/grades/', GradeList.as_view(), name='grade_list'),
    path('<slug:school_slug>/level/<int:level_id>/grade/<int:grade_id>/sections/', SectionList.as_view(), name='section_list'),

    path('<slug:school_slug>/register_general_assistance/entrance/<str:dni>/', RegisterEntranceGeneralAssistance.as_view(), name='register_entrance_general_assistance'),
    path('<slug:school_slug>/register_general_assistance/exit/<str:dni>', RegisterEntranceGeneralAssistance.as_view(), name='register_entrance_general_assistance'),
    path('<slug:school_slug>/register_course_assistance/<int:course_id>/<str:dni>/', RegisterEntranceGeneralAssistance.as_view(), name='register_entrance_general_assistance'),

    path('login', login, name='login'),
    path('register_assistance', register_assistance, name='register_assistance'),

    path('receive-data', receive_data, name='receive_data'),
    path('get-info-school', get_info_school, name='get_info_school'),
    path('get-students-info', get_students_info, name='get_students_info'),
]