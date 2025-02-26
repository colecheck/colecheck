from django.shortcuts import render
from django.views import View
from apps.school.models import School
from apps.assistance.models import GeneralAssistance, DetailGeneralAssistance, Assistance, DetailAssistance
from datetime import date, datetime, timedelta, time
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from apps.school.models import EducationLevel, Grade, Section, Course
from apps.student.models import Student, Parent
from django.template.defaultfilters import slugify
from random import random

# Create your views here.

def home(request):
    #events = Event.objects.all()
    events = {}
    return render(request, "director/Home.html", {'events':events})

def general_assistance(request):
    return render(request, "director/GeneralAssistance.html")

def course_assistance(request):
    return render(request, "director/CourseAssistance.html")

def create_student(request):
    return render(request, "director/CreateStudent.html")

def get_or_create_school(school_name):
    new_school, created = School.objects.get_or_create(name=school_name,
                                            slug=slugify(school_name))
    return new_school, created

def generate_general_assistances_dates(school_obj):
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    delta = timedelta(days=1)

    while start_date <= end_date:
        new_assistance, created = GeneralAssistance.objects.get_or_create(date=start_date, school=school_obj)
        start_date += delta

def get_or_create_user(username, first_name, last_name):
    user_obj, created = User.objects.get_or_create(username=username, first_name=first_name, last_name=last_name)
    if created:
        user_obj.set_password('qwerty.123')
        user_obj.save()
    return user_obj, created

def get_or_create_teacher(username, first_name, last_name, school_obj):
    user_obj, created = get_or_create_user(username, first_name, last_name)
    teacher_obj, created = Teacher.objects.get_or_create(user=user_obj, dni="29292929", school=school_obj)
    return teacher_obj, created

def get_or_create_auxiliar(username, first_name, last_name, school_obj):
    user_obj, created = get_or_create_user(username, first_name, last_name)
    auxiliar_obj, created = Auxiliar.objects.get_or_create(user=user_obj, dni="29292929", school=school_obj)
    return auxiliar_obj, created 

def get_or_create_principal(username, first_name, last_name, school_obj):
    user_obj, created = get_or_create_user(username, first_name, last_name)
    principal_obj, created = Principal.objects.get_or_create(user=user_obj, dni="29292929", school=school_obj)
    return principal_obj, created 

def generate_levels_grades_sections(school_obj):
    primaria, created = EducationLevel.objects.get_or_create(name="Primaria", school=school_obj)
    secundaria, created = EducationLevel.objects.get_or_create(name="Secundaria", school=school_obj)

    primero_sec, created = Grade.objects.get_or_create(name='Primero', short_name="1", school=school_obj, level=secundaria)
    segundo_sec, created = Grade.objects.get_or_create(name='Segundo', short_name="2", school=school_obj, level=secundaria)
    tercero_sec, created = Grade.objects.get_or_create(name='Tercero', short_name="3", school=school_obj, level=secundaria)
    cuarto_sec, created = Grade.objects.get_or_create(name='Cuarto', short_name="4", school=school_obj, level=secundaria)
    quinto_sec, created = Grade.objects.get_or_create(name='Quinto', short_name="5", school=school_obj, level=secundaria)

    pri_sec_a, created = Section.objects.get_or_create(grade=primero_sec, name="A")
    pri_sec_b, created = Section.objects.get_or_create(grade=primero_sec, name="B")
    pri_sec_c, created = Section.objects.get_or_create(grade=primero_sec, name="C")
    pri_sec_d, created = Section.objects.get_or_create(grade=primero_sec, name="D")

    seg_sec_a, created = Section.objects.get_or_create(grade=segundo_sec, name="A")
    seg_sec_b, created = Section.objects.get_or_create(grade=segundo_sec, name="B")
    seg_sec_c, created = Section.objects.get_or_create(grade=segundo_sec, name="C")
    seg_sec_d, created = Section.objects.get_or_create(grade=segundo_sec, name="D")

    ter_sec_a, created = Section.objects.get_or_create(grade=tercero_sec, name="A")
    ter_sec_b, created = Section.objects.get_or_create(grade=tercero_sec, name="B")
    ter_sec_c, created = Section.objects.get_or_create(grade=tercero_sec, name="C")
    ter_sec_d, created = Section.objects.get_or_create(grade=tercero_sec, name="D")

    cua_sec_a, created = Section.objects.get_or_create(grade=cuarto_sec, name="A")
    cua_sec_b, created = Section.objects.get_or_create(grade=cuarto_sec, name="B")
    cua_sec_c, created = Section.objects.get_or_create(grade=cuarto_sec, name="C")
    cua_sec_d, created = Section.objects.get_or_create(grade=cuarto_sec, name="D")

    qui_sec_a, created = Section.objects.get_or_create(grade=quinto_sec, name="A")
    qui_sec_b, created = Section.objects.get_or_create(grade=quinto_sec, name="B")
    qui_sec_c, created = Section.objects.get_or_create(grade=quinto_sec, name="C")
    qui_sec_d, created = Section.objects.get_or_create(grade=quinto_sec, name="D")


def generate_random_general_assistances(student_obj):
    school_obj = student_obj.school
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    delta = timedelta(days=1)

    while start_date <= end_date:
        gen_assistance = GeneralAssistance.objects.get(date=start_date, school=school_obj)
        d_gen_assist, created = DetailGeneralAssistance.objects.get_or_create(general_assistance=gen_assistance, student=student_obj)
        if created:
            dice = random()
            if dice < 0.5:
                d_gen_assist.state = "Presente"
                d_gen_assist.time = time(12,0,0)
                other_dice = random()
                if other_dice < 0.8:
                    d_gen_assist.exit_state = "Salio"
                    d_gen_assist.exit_time = time(14,0,0)
                else:
                    d_gen_assist.exit_state = "Aun no salio"
            elif dice < 0.7:
                d_gen_assist.state = DetailGeneralAssistance.AttendanceStatus.TARDANZA
                d_gen_assist.time = time(13,0,0)
                other_dice = random()
                if other_dice < 0.8:
                    d_gen_assist.exit_state = "Salio"
                    d_gen_assist.exit_time = time(15,0,0)
                else:
                    d_gen_assist.exit_state = "Aun no salio"
            elif dice < 0.8:
                d_gen_assist.state = DetailGeneralAssistance.AttendanceStatus.FALTA
                d_gen_assist.exit_state = "Aun no salio"
            else:
                d_gen_assist.state = DetailGeneralAssistance.AttendanceStatus.DESCONOCIDO
                d_gen_assist.exit_state = "Desconocido"
            d_gen_assist.save()
        start_date += delta



def int_from_weekday(weekday):
    days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    return days.index(weekday)



def generate_random_course_assistances(student_obj, course_obj):
    for assistance in course_obj.assistances.all():
        course_assistance, created = DetailAssistance.objects.get_or_create(assistance=assistance, student=student_obj)
        if created:
            dice = random()
            if dice < 0.7:
                course_assistance.state = "Presente"
                course_assistance.time = time(12,0,0)
            elif dice < 0.8:
                course_assistance.state = "Tardanza"
                course_assistance.time = time(14,0,0)
            else:
                course_assistance.state = "Falta"
        course_assistance.save()
                    

def get_or_create_student(first_name, last_name, dni, school_obj, ed_level, grade, section, parent_name, parent_last, courses):
    level_obj, created = EducationLevel.objects.get_or_create(name=ed_level, school=school_obj)
    grade_obj, created = Grade.objects.get_or_create(short_name=grade, level=level_obj)
    section_obj, created = Section.objects.get_or_create(name=section, grade=grade_obj)
    parent_obj, created = Parent.objects.get_or_create(first_name=parent_name, last_name=parent_last, dni="29292929", phone_number="+51999999999")
    student_obj, created = Student.objects.get_or_create(first_name=first_name, last_name=last_name, school=school_obj,
                                                         dni=dni,
                                                         level=level_obj, grade=grade_obj,
                                                        section=section_obj, parent=parent_obj)
    student_obj.save()
    for course in courses:
        student_obj.courses.add(course)

    generate_random_general_assistances(student_obj)

    for course in courses:
        generate_random_course_assistances(student_obj, course)
    return student_obj, created

def get_or_create_course(name, short_name, teacher_obj, ed_level, grade, section=None):
    school = teacher_obj.school
    ed_level_obj, created = EducationLevel.objects.get_or_create(name=ed_level, school=school)
    grade_obj, created = Grade.objects.get_or_create(short_name=grade, level=ed_level_obj)
    if section:
        section_obj, created = Section.objects.get_or_create(name=section, grade=grade_obj)
        course_obj, created = Course.objects.get_or_create(name=name, short_name=short_name, teacher=teacher_obj, grade=grade_obj, section=section_obj, school=school)
        return course_obj, created
    else: 
        course_obj, created = Course.objects.get_or_create(name=name, short_name=short_name, teacher=teacher_obj, grade=grade, school=school)
        return course_obj, created
    
class PopulateView(View):
    
    def get(self, request, *args, **kwargs):

        san_jeronimo, created = get_or_create_school('San Jeronimo')
        mariano_melgar, created = get_or_create_school('Mariano Melgar')
        ie_mixto, created = get_or_create_school('IE Mixto')
        
        generate_general_assistances_dates(san_jeronimo)
        generate_general_assistances_dates(mariano_melgar)
        generate_general_assistances_dates(ie_mixto)

        moises, created = get_or_create_teacher('moises', 'Moises', 'Casaverde', san_jeronimo)
        prof, created = get_or_create_teacher('profesor', 'Profesor', 'Uno', san_jeronimo)
        prof2, created = get_or_create_teacher('profesor2', 'Profesor', 'Dos', san_jeronimo)


        john, created = get_or_create_auxiliar('john', 'John', 'Sanchez', san_jeronimo)
        yamil, created = get_or_create_principal('yamil', 'Yamil', 'Llampi', san_jeronimo)

        generate_levels_grades_sections(san_jeronimo)

        mat1a_sj, crated = get_or_create_course(name="Matematica - 1A", short_name="MAT-1A", teacher_obj=moises, ed_level="Secundaria", grade="1", section="A")

        com1a_sj, crated = get_or_create_course(name="Comunicacion - 1A", short_name="COM-1A", teacher_obj=moises, ed_level="Secundaria", grade="1", section="A")
        
        ct1a_sj, crated = get_or_create_course(name="Ciencia y Tecnologia - 1A", short_name="CIE-3A", teacher_obj=moises, ed_level="Secundaria", grade="1", section="A")
        
        mat2a_sj, crated = get_or_create_course(name="Matematica - 2A", short_name="MAT-2A", teacher_obj=moises, ed_level="Secundaria", grade="2", section="A")

        courses_1a = [mat1a_sj, com1a_sj, ct1a_sj]

        st1, created = get_or_create_student("Matias", "Rodriguez", "89981212", san_jeronimo, "Secundaria", "1", "A", "Padre", "Uno", courses_1a)
        st2, created = get_or_create_student("Leon", "Rodriguez", "89981213", san_jeronimo, "Secundaria", "1", "A", "Padre", "Dos", courses_1a)
        st3, created = get_or_create_student("Alice", "Macedo", "89981214", san_jeronimo, "Secundaria", "1", "A", "Padre", "Tres", courses_1a)


        return redirect(reverse("school_app:home"))

