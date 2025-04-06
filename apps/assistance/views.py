import json
from datetime import datetime, date, timedelta, time
from http import HTTPStatus
import aiohttp
from django.db.models import Count, Q
from django.http.response import HttpResponse
from common.util.user_belongs_to_school import user_belongs_to_school
from common.util.get_or_none import get_or_none
from common.util.time_in_range import time_in_range
from common.util.add_user_type_to_context import add_user_type_to_context
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ImproperlyConfigured
from apps.assistance.models import Assistance, DetailAssistance
from apps.school.models import Course, ScheduleBlock, Grade, Section, EducationLevel, School, PhotocheckDuplicates
from apps.student.models import Student, Parent
from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from apps.system.models import NgrokConfiguration, StudentDataDefault
from apps.assistance.models import Assistance, GeneralAssistance, DetailGeneralAssistance
from common.util.get_school import get_school
from common.util.add_school_to_context import add_school_to_context
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import pandas as pd
import requests
import base64
import time
import re
from pathlib import Path

from django.db import transaction
from collections import defaultdict

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

MONTHS = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre"
]

ORDINAL_TO_NUMBER = {
    "Primero": 1,
    "Segundo": 2,
    "Tercero": 3,
    "Cuarto": 4,
    "Quinto": 5,
    "Sexto": 6,
    "Séptimo": 7,
    "Octavo": 8,
    "Noveno": 9,
    "Decimo": 10
}

BASE_DIR = Path(__file__).resolve().parent.parent
with open('secret.json') as f:
    secret = json.loads(f.read())


def get_secret(secret_name, secrets=secret):
    try:
        return secrets[secret_name]
    except Exception as e:
        message = f'La variable {secret_name} no existe [{e}]'
        raise ImproperlyConfigured(message)


def paginate_data(request, data, num_per_page):
    paginator = Paginator(data, num_per_page)
    page = request.GET.get('page')

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = paginator.page(paginator.num_pages)

    return paginated_data


# ---------------------------------------------------------------------------------------#
# --------------------------------AUXILIAR----------------------------------------------#
# ---------------------------------------------------------------------------------------#


class TakeEntranceAssistanceView(LoginRequiredMixin, TemplateView):
    template_name = 'assistant/TakeEntranceAssistance.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_obj = get_school(self.request.user)
        context['school'] = school_obj
        context['students'] = school_obj.students.all()
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            school = get_school(request.user)
            auxiliar = get_or_none(Auxiliar, user=user_id)
            if auxiliar is None:
                return redirect(reverse('school_app:school_home', kwargs={'slug': school.slug}))
        return super().dispatch(request, *args, **kwargs)


class CheckFotocheckView(LoginRequiredMixin, TemplateView):
    template_name = 'assistant/CheckFotocheck.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_obj = get_school(self.request.user)
        context['school'] = school_obj
        context['students'] = school_obj.students.all()
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            school = get_school(request.user)
            auxiliar = get_or_none(Auxiliar, user=user_id)
            if auxiliar is None:
                return redirect(reverse('school_app:school_home', kwargs={'slug': school.slug}))
        return super().dispatch(request, *args, **kwargs)


from .service import FactoryFotocheck


class CreateFotocheckView(LoginRequiredMixin, TemplateView):
    template_name = 'assistant/CreateFotocheck.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school
        context['students'] = school.students.all()

        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')

        ed_levels = school.levels.all()

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        ed_level = None
        grade = None
        if select_ed_level:
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(level=ed_level, name=select_grade)
            sections = grade.sections.all()
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().name

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(grade=grade, name=select_section)
            context['one_section'] = True
            context['section'] = section

        context['levels'] = ed_levels

        add_user_type_to_context(self.request.user, context)

        return context


@csrf_exempt
def send_create_fotocheck(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)
            section_id_str = data["section"]
            amount = data["amount"]
            manyStudent = data["manyStudent"]
            school = get_school(request.user)

            if manyStudent:

                section_id = int(section_id_str)
                section = get_object_or_404(Section, id=section_id)

                students = list(section.students.all())
            else:
                student = Student.objects.get(school=school, dni=section_id_str)
                students = [student]

                photocheck_duplicate = PhotocheckDuplicates.objects.create(
                    user=request.user,
                    school=school,
                    student=student,
                    amount=amount
                )

            factory = FactoryFotocheck()

            if school.use_card:
                buff = factory.create_pdf_from_student_card(students, slug)
            else:
                buff = factory.create_pdf_from_students(students, slug)

            buff_base64 = base64.b64encode(buff.getvalue()).decode('utf-8')

            return JsonResponse({'student_fotochecks_PDF': f'{buff_base64}'})
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'Fotochecks no creados',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# @csrf_exempt
# def send_create_qrs(request, slug):
#     if request.method == 'POST':
#         try:
#             data_request = request.POST.get('data')
#             data = json.loads(data_request)
#             level_id = data["level_id"]
#             grade_id = data["grade_id"]
#             section_id = data["section"]
#
#             section = get_object_or_404(Section, id=section_id)
#
#             students = list(section.students.all())
#
#             factory = FactoryFotocheck()
#             buff = factory.create_qr_pdf_from_students(students, slug)
#             buff_base64 = base64.b64encode(buff.getvalue()).decode('utf-8')
#
#             return JsonResponse({'student_fotochecks_PDF': f'{buff_base64}'})
#         except (KeyError, json.JSONDecodeError) as e:
#             return JsonResponse({
#                 'title': 'Error',
#                 'content': "QR's no creados",
#                 'error': str(e)
#             }, status=404)
#     else:
#         return JsonResponse({'error': 'Metodo no permitido'}, status=405)


class GeneralAssistanceReportView(LoginRequiredMixin, TemplateView):
    template_name_auxiliar = 'assistant/AssistantGeneralAssistance.html'
    template_name_director = 'director/GeneralAssistance.html'

    template_name_ = 'assistant/AssistantGeneralAssistance.html'  # default

    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')
        select_month = self.request.GET.get('month')
        select_daterange_start = self.request.GET.get('daterange-start')
        select_daterange_end = self.request.GET.get('daterange-end')
        select_date_type = self.request.GET.get('dates-type')

        if select_date_type:
            if select_date_type == "daterange":
                if not select_daterange_start:
                    select_daterange_start = timezone.now().date().replace(day=1)
                    select_daterange_end = select_daterange_start.replace(month=select_daterange_start.month % 12 + 1,
                                                                          day=1) - timedelta(days=1)
            if select_date_type == "month":
                if not select_month:
                    select_month = timezone.now().month
                elif select_month == "all":
                    select_month = None
        else:
            select_date_type = "month"
            # Selecciona el mes actual si no se especifica el mes en el query
            if not select_month:
                select_month = timezone.now().month
            elif select_month == "all":
                select_month = None

        ed_levels = school.levels.all()
        assistances = school.general_assistances.all()
        students = school.students.all()

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        context['one_month'] = False
        ed_level = None
        grade = None
        if select_ed_level:
            students = students.filter(level__name__contains=select_ed_level)
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(level=ed_level, name=select_grade)
            sections = grade.sections.all()
            students = grade.students.all()
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().name

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(grade=grade, name=select_section)
            students = section.students.all()
            context['one_section'] = True
            context['section'] = section

        if select_month:
            assistances = assistances.filter(date__month=int(select_month))
            context['one_month'] = True
            context['month'] = int(select_month)

        if select_daterange_start:
            assistances = assistances.filter(date__gte=select_daterange_start, date__lte=select_daterange_end)
            context["daterange_start"] = select_daterange_start
            context["daterange_end"] = select_daterange_end

        paginated_students = paginate_data(self.request, students, 15)

        context['dates_type'] = select_date_type
        context['assistances'] = assistances
        context['students'] = paginated_students
        context['levels'] = ed_levels

        # Recopilar datos para el gráfico
        attendance_data = defaultdict(lambda: {'presente': 0, 'tardanza': 0, 'falta': 0})

        for assistance in assistances:
            for detail in assistance.details_general_assistance.filter(student__in=students):
                date = assistance.date.strftime('%Y-%m-%d')
                if detail.state == 'Presente':
                    attendance_data[date]['presente'] += 1
                elif 'Tardanza' in detail.state:
                    attendance_data[date]['tardanza'] += 1
                elif 'Falta' in detail.state:
                    attendance_data[date]['falta'] += 1

        context['attendance_dates'] = json.dumps(list(attendance_data.keys()))
        context['attendance_presente'] = json.dumps([data['presente'] for data in attendance_data.values()])
        context['attendance_tardanza'] = json.dumps([data['tardanza'] for data in attendance_data.values()])
        context['attendance_falta'] = json.dumps([data['falta'] for data in attendance_data.values()])

        add_user_type_to_context(self.request.user, context)

        return context

    def get_template_names(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            is_auxiliar = get_or_none(Auxiliar, user=user_id)
            is_director = get_or_none(Principal, user=user_id)
            if is_auxiliar is not None:
                return [self.template_name_auxiliar]
            elif is_director is not None:
                return [self.template_name_director]
        return [self.template_name_]

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            auxiliar = get_or_none(Auxiliar, user=user_id)
            director = get_or_none(Principal, user=user_id)
            if auxiliar is None and director is None:
                return redirect('school_app:home')
            if not user_belongs_to_school(self.request.user, **kwargs):
                return redirect(reverse('school_app:home'))
        return super().dispatch(request, *args, **kwargs)


from .service import FactoryReports


@csrf_exempt
def download_general_assistance(request, slug):
    if (request.method == 'GET'):
        school = get_school(request.user)
        students = Student.objects.filter(school=school)
        selected_level = request.GET.get('level')
        selected_grade = request.GET.get('grade')
        selected_section = request.GET.get('section')
        selected_month = request.GET.get('month')

        if selected_level:
            students = students.filter(level__name__icontains=selected_level)
        else:
            levels = school.levels.all()
            if levels.count() == 1:
                selected_level = levels.first().name
            else:
                selected_level = 'General'

        # if selected_section == None:
        #    grade = Grade.objects.get(level=selected_level, name=selected_grade)
        #    sections = grade.sections.all()
        #    if(sections.count() == 1):
        #        selected_section = sections.first().name

        if not selected_month or selected_month == 'all':
            selected_month = datetime.now().month

        if selected_grade:
            students = students.filter(grade__name__icontains=selected_grade)
        else:
            if selected_level != 'General':
                grades = school.grades.filter(level__name__icontains=selected_level).all()
                if grades.count() == 1:
                    selected_grade = grades.first().name
                else:
                    selected_grade = 'General'
            else:
                selected_grade = 'General'

        if selected_section:
            students = students.filter(section__name__icontains=selected_section)
        else:
            if selected_grade != 'General':
                sections = Grade.objects.get(school=school, name__icontains=selected_grade,
                                             level__name__icontains=selected_level).sections.all()
                if sections.count() == 1:
                    selected_section = sections.first().name
                else:
                    selected_section = 'General'
            else:
                selected_section = 'General'

        factory_reports = FactoryReports()
        user_request = f'{request.user.first_name} {request.user.last_name}'
        context = {
            'month': int(selected_month),
            'school': school,
            'level': selected_level,
            'grade': selected_grade,
            'section': selected_section,
        }
        wb = factory_reports.create_general_report(students, user_request, context)

    # Configurar la respuesta para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=registro-asistencia.xlsx'

    # Guardar el libro de Excel en la respuesta
    wb.save(response)
    return response


@csrf_exempt
def download_course_assistance(request, slug):
    school = get_school(request.user)

    selected_id_course = request.GET.get('course')
    selected_month = request.GET.get('month')

    course = None
    students = None

    if selected_id_course:
        course = Course.objects.get(id=selected_id_course)

    if not selected_month or selected_month == 'all':
        selected_month = datetime.now().month

    if course:
        students = Student.objects.filter(courses=course)

    section = course.section.name
    grade = course.grade.name
    level = course.grade.level.name

    factory_reports = FactoryReports()
    user_request = f'{request.user.first_name} {request.user.last_name}'
    context = {
        'month': int(selected_month),
        'school': school,
        'level': level,
        'grade': grade,
        'section': section,
        'course': course
    }
    wb = factory_reports.create_course_report(students, user_request, context)

    # if select_month:
    #     assistances_month_course = Assistance.objects.filter(course=select_course, date__month=int(select_month))
    #     month = int(select_month)
    #
    # factory_reports = FactoryReports()
    # wb = factory_reports.create_course_report(students, select_course, assistances_month_course, month)

    # Configurar la respuesta para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={ORDINAL_TO_NUMBER[grade]}{section} - {course.name}.xlsx'

    # Guardar el libro de Excel en la respuesta
    wb.save(response)
    return response


class AssistanceReport(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/TeacherAssistanceReport.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school_obj = get_school(self.request.user)
        context['school'] = school_obj

        select_id_course = self.request.GET.get('course')
        select_month = self.request.GET.get('month')
        select_course = None

        if select_id_course:
            select_course = Course.objects.get(id=select_id_course)

        if not select_month or select_month == 'all':
            select_month = datetime.now().month

        teacher_obj = Teacher.objects.get(user=self.request.user)
        teacher_courses = teacher_obj.courses.all()

        context['courses'] = teacher_courses

        if select_course:
            assistances = select_course.assistances.all()
            students = select_course.students.all()

            paginated_students = paginate_data(self.request, students, 15)
            context['one_course'] = True
            context['course'] = select_course
            context['assistances'] = assistances
            context['students'] = paginated_students

            if select_month:
                assistances = assistances.filter(date__month=int(select_month))
                context['one_month'] = True
                context['month'] = int(select_month)
                context['assistances'] = assistances

        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            teacher = get_or_none(Teacher, user=user_id)
            if teacher is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


class AllCourseAssistanceReport(LoginRequiredMixin, TemplateView):
    template_name = 'director/CourseAssistance.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        select_id_teacher = self.request.GET.get('teacher')
        select_id_course = self.request.GET.get('course')
        select_month = self.request.GET.get('month')
        select_course = None
        select_teacher = None

        context['teachers'] = school.teachers.all()

        if select_id_teacher:
            select_teacher = Teacher.objects.get(id=select_id_teacher)

        if select_id_course:
            select_course = Course.objects.get(id=select_id_course)

        if not select_month:
            select_month = datetime.now().month
        elif select_month == "all":
            select_month = None

        context['one_teacher'] = False
        context['one_course'] = False
        context['one_month'] = False

        if select_teacher:
            teacher_courses = Course.objects.filter(teacher=select_teacher)
            context['courses'] = teacher_courses
            context['one_teacher'] = True

        if select_course:
            assistances = select_course.assistances.all()
            students = select_course.students.all()

            paginated_students = paginate_data(self.request, students, 15)
            context['one_course'] = True
            context['course'] = select_course
            context['assistances'] = assistances
            context['students'] = paginated_students

            if select_month:
                assistances = assistances.filter(course=select_course, date__month=int(select_month))
                context['one_month'] = True
                context['month'] = int(select_month)
                context['assistances'] = assistances
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


def int_from_weekday(weekday):
    days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    return days.index(weekday)


class TakeAssistanceView(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/TeacherTakeCourseAssistance.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_obj = Teacher.objects.get(user=self.request.user.id)
        context['school'] = teacher_obj.school

        current_date = timezone.now().date()

        assistance_list = []
        block_list = []

        for course in teacher_obj.courses.all():
            # Ya que el horario puede cambiar, los bloques activos representan a los que funcionan a dia de hoy,
            # Si se desea cambiar el horario y por lo tanto ya no usar bloques, se consideraran inactivos y no
            # se eliminaran de la base de datos
            active_blocks = course.blocks.all().filter(status=ScheduleBlock.ScheduleBlockStatus.ACTIVE)
            for block in course.blocks.all():
                if int_from_weekday(block.day) == current_date.weekday():
                    if block.assistances.all().filter(date=current_date).exists():
                        assistance = block.assistances.all().get(date=current_date)
                        assistance_list.append(assistance)
                    else:
                        block_list.append(block)

        context['assistances'] = assistance_list
        context['blocks'] = block_list

        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            teacher = get_or_none(Teacher, user=user_id)
            if teacher is None:
                return redirect('school_app:home')
            current_date = timezone.now().date()

            assistance_list = []
            for course in teacher.courses.all():
                for block in course.blocks.all():
                    if int_from_weekday(block.day) == current_date.weekday():
                        for assistance in block.assistances.all():
                            if assistance.date == current_date:
                                assistance_list.append(assistance)

            # if len(assistance_list) == 1:
            #    return redirect(reverse('assistance_app:edit_course_assistance', kwargs={'slug': teacher.school.slug, 'pk': assistance_list[0].id }))

        return super().dispatch(request, *args, **kwargs)


class EditAssistanceView(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/TeacherEditCourseAssistance.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        assistance_id = kwargs.get('pk')
        assistance = get_object_or_404(Assistance, id=assistance_id)

        context = super().get_context_data(**kwargs)
        teacher_obj = Teacher.objects.get(user=self.request.user.id)
        context['school'] = teacher_obj.school
        course_obj = assistance.block.course
        context['course'] = course_obj
        context['students'] = course_obj.students.all()
        context['assistance'] = assistance
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            teacher = get_or_none(Teacher, user=user_id)
            if teacher is None:
                return redirect('school_app:home')

            assistance_id = kwargs.get('pk')
            assistance = get_object_or_404(Assistance, id=assistance_id)

            if assistance.block.course.teacher != teacher:
                return redirect('school_app:home')

        return super().dispatch(request, *args, **kwargs)


class AddAssistanceView(LoginRequiredMixin, TemplateView):
    template_name = 'director/CreateStudent.html'
    login_url = reverse_lazy('login')


class JustifyAssistanceView(LoginRequiredMixin, TemplateView):
    template_name = 'assistant/JustifyAssistance.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_obj = get_school(self.request.user)
        context['school'] = school_obj
        context['students'] = school_obj.students.all()

        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            auxiliar = get_or_none(Auxiliar, user=user_id)
            director = get_or_none(Principal, user=user_id)
            if auxiliar is None and director is None:
                return redirect('school_app:home')
            if not user_belongs_to_school(self.request.user, **kwargs):
                return redirect(reverse('school_app:home'))
        return super().dispatch(request, *args, **kwargs)


class JustificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'assistant/Justifications.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = timezone.now().date()
        school_obj = get_school(self.request.user)
        context['school'] = school_obj
        context['students'] = school_obj.students.all()
        context['today_justs'] = DetailGeneralAssistance.objects.filter(general_assistance__school=school_obj,
                                                                        general_assistance__date=current_date,
                                                                        state__in=[
                                                                            DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_PEDIDA,
                                                                            DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_REGISTRADA,
                                                                            DetailGeneralAssistance.AttendanceStatus.FALTA_JUSTIFICADA]).order_by(
            '-general_assistance__date', '-time')
        context['prev_justs'] = DetailGeneralAssistance.objects.filter(general_assistance__school=school_obj,
                                                                       general_assistance__date__lt=current_date,
                                                                       state__in=[
                                                                           DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_PEDIDA,
                                                                           DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_REGISTRADA,
                                                                           DetailGeneralAssistance.AttendanceStatus.FALTA_JUSTIFICADA]).order_by(
            '-general_assistance__date', '-time')
        context['pend_justs'] = DetailGeneralAssistance.objects.filter(general_assistance__school=school_obj,
                                                                       general_assistance__date__gt=current_date,
                                                                       state__in=[
                                                                           DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_PEDIDA,
                                                                           DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_REGISTRADA,
                                                                           DetailGeneralAssistance.AttendanceStatus.FALTA_JUSTIFICADA]).order_by(
            '-general_assistance__date', '-time')
        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            auxiliar = get_or_none(Auxiliar, user=user_id)
            director = get_or_none(Principal, user=user_id)
            if auxiliar is None and director is None:
                return redirect('school_app:home')
            if not user_belongs_to_school(self.request.user, **kwargs):
                return redirect(reverse('school_app:home'))
        return super().dispatch(request, *args, **kwargs)


class DirectorSettings(LoginRequiredMixin, TemplateView):
    template_name = 'director/Settings.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_obj = get_school(self.request.user)
        context['school'] = school_obj
        levels = school_obj.levels.all()
        context['levels'] = levels
        levels_json = json.dumps([{'name': level.name} for level in levels])
        context['levels_json'] = levels_json
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            assistant = get_or_none(Principal, user=user_id)
            if assistant is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


class DailyAssistanceReportView(LoginRequiredMixin, TemplateView):
    template_name_ = 'director/DailyReport.html'
    template_name_auxiliar = 'assistant/AssistantDailyReport.html'
    template_name_director = 'director/DailyReport.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school
        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')
        select_date_str = self.request.GET.get('date')
        select_state = self.request.GET.get('state')

        # Selecciona el mes actual si no se especifica el mes en el query
        select_date = None
        if not select_date_str:
            select_date = timezone.now().date()
        else:
            select_date = datetime.strptime(select_date_str, "%Y-%m-%d").date()
        ed_levels = school.levels.all()
        students = school.students.all()
        general_assistance = school.general_assistances.get(date=select_date)

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        context['one_month'] = False
        ed_level = None
        grade = None
        details = general_assistance.details_general_assistance.all()

        if select_ed_level:
            details = details.filter(student__level__name=select_ed_level)
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(level=ed_level, name=select_grade)
            sections = grade.sections.all()
            details = details.filter(student__grade=grade)
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().name

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(grade=grade, name=select_section)
            details = details.filter(student__section=section)
            context['one_section'] = True
            context['section'] = section
        if select_state:
            if select_state == "Salio" or select_state == "Aun no salio":
                details = details.filter(exit_state=select_state)
            else:
                details = details.filter(state=select_state)

        paginated_details = paginate_data(self.request, details, 15)

        details_count = details.count()
        if select_state == 'Presente':
            select_state = 'Temprano'

        if not select_state:
            details_count = details.filter(state='Presente').count() + details.filter(state='Tardanza').count()

        context['select_state'] = select_state if select_state is not None else 'Asistencia'
        context['details_count'] = details_count
        context['date'] = select_date
        context['details'] = paginated_details
        context['levels'] = ed_levels

        # chart.js
        attendance_data = details.aggregate(
            Presente=Count('state', filter=Q(state='Presente')),
            Tardanza=Count('state', filter=Q(state='Tardanza')),
            Falta=Count('state', filter=Q(state='Falta'))
        )

        attendance_data_json = json.dumps(attendance_data)
        context['attendance_data'] = attendance_data_json

        add_user_type_to_context(self.request.user, context)

        return context

    def get_template_names(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            is_auxiliar = get_or_none(Auxiliar, user=user_id)
            is_director = get_or_none(Principal, user=user_id)
            if is_auxiliar is not None:
                return [self.template_name_auxiliar]
            elif is_director is not None:
                return [self.template_name_director]
        return [self.template_name_]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = request.user.id
            auxiliar = get_or_none(Auxiliar, user=user_id)
            director = get_or_none(Principal, user=user_id)
            if auxiliar is None and director is None:
                return redirect('school_app:home')
            if not user_belongs_to_school(request.user, **kwargs):
                return redirect(reverse('school_app:home'))
        return super().dispatch(request, *args, **kwargs)


TOKEN = 'Bearer EAAKTQGZAFMwgBO8zoPSrLnH8XljqtvYBJFOZBoeRFIIHoV7XXGaRJmuzzlyVvsB69tXVbfFEJfEI0LjGkPVKsAoGLirZCdLctzG1lWqkZAyDvc39v6ZAc0NBm2VxYEViuwZAsMsnHzEB00R65ZCwNrRraXcXWxnc5ijRK95p1E4fwViz5MCi0uj6bZC8C1OdRL3jzO3KSt7sSZAiSsZB0ZCm8wZD'
URL = 'https://graph.facebook.com/v18.0/238858015980284/messages'


def sendWhastAppMessage(phoneNumber, list_of_data):
    headers = {"Authorization": TOKEN,
               "Content-Type": "application/json"
               }
    payload = {"messaging_product": "whatsapp",
               "to": phoneNumber,
               "type": "template",
               "template": {
                   "name": "mi_plantilla_1",
                   "language": {
                       "code": "es"
                   },
                   "components": [
                       {
                           "type": "BODY",
                           "parameters": [
                               {
                                   "type": "text",
                                   "text": list_of_data[0]
                               },
                               {
                                   "type": "text",
                                   "text": list_of_data[1]
                               },
                               {
                                   "type": "text",
                                   "text": list_of_data[2]
                               }
                           ]
                       }
                   ]
               }
               }
    response = requests.post(URL, headers=headers, json=payload)
    return response.json()



def send_whatsapp_message_to_parent(student, attendance_type, in_classroom=False, communicated=False):
    print("Enviando mensaje de WhatsApp...: ", student.school.slug)
    current_time = datetime.now().strftime("%H:%M:%S")
    communicated_msg = student.school.communicated if communicated else ''

    data = {
        "time_assistance": current_time,
        "student": f"{student.first_name} {student.last_name}",
        "phoneNumber": student.parent.phone_number,
        "type_assistance": attendance_type,
        "classroom": in_classroom,
        "isCommunicated": communicated,
        "communicated": communicated_msg
    }

    # Determinar la URL según el slug
    if student.school.slug == "ie-san-martin-de-porres-circa":
        url = "http://157.230.81.198:3000/wapp-web/senddReport"
    elif student.school.slug == "institucion-educativa-particular-nanterre":
        url = "http://157.230.81.198:3001/wapp-web/senddReport"
    else:
        print(f"⚠️ No se encontró una URL para el slug: {student.school.slug}")
        return
    
    headers = {'Content-Type': 'application/json'}


    response = requests.post(url, data=json.dumps(data), headers=headers)
    response.raise_for_status()
        
    print(f"🔹 Respuesta cruda de la API: {response.text}")  # Imprime la respuesta antes de intentar parsear JSON
        
    # Intentar obtener JSON solo si la respuesta tiene contenido
    if response.text.strip():
        print(f"✅ Mensaje enviado: {response.json()}")
    else:
        print("⚠️ La API respondió con un cuerpo vacío.")
    


    """
    ngrok_url = NgrokConfiguration.objects.first().host
    current_time = datetime.now().strftime("%H:%M:%S")
    communicated_msg = student.school.communicated if communicated else ''
    phone_number = student.parent.phone_number
    have_whatsapp = student.parent.whatsapp_phone

    data = {
        'time_assistance': current_time,
        'student': f'{student.first_name}, {student.last_name}',
        'phone_number': phone_number,
        'have_whatsapp': have_whatsapp,
        'type_assistance': attendance_type,
        'classroom': in_classroom,
        'is_communicated': communicated,
        'communicated': communicated_msg
    }

    json_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    url = f'{ngrok_url}/asistencia-diario'
    requests.post(url, data=json_data, headers=headers)
    """


def open_general_assistance(general_assistance):
    general_assistance.state = "Open"
    general_assistance.save()
    for detail_assistance in general_assistance.details_general_assistance.all():
        if detail_assistance.state == DetailGeneralAssistance.AttendanceStatus.DESCONOCIDO:
            detail_assistance.state = DetailGeneralAssistance.AttendanceStatus.FALTA
            detail_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_NO_MARCADA
            detail_assistance.save()


# Manejar la tardanza y si tenia justificacion
def handle_assistance_state(detail_assistance, student_obj):
    tolerance_time = (datetime.combine(date(1, 1, 1), student_obj.level.entrance_time) + timedelta(
        minutes=student_obj.level.tolerance)).time()  # La tolerancia debe depender del colegio
    if tolerance_time < detail_assistance.time:
        if detail_assistance.state == DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_PEDIDA:
            detail_assistance.state = DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_REGISTRADA
        else:
            detail_assistance.state = DetailGeneralAssistance.AttendanceStatus.TARDANZA
    else:
        detail_assistance.state = DetailGeneralAssistance.AttendanceStatus.PRESENTE
    detail_assistance.save()


# Vista POST, recibe el json con el DNI del estudiante y lo registra a la asistencia general de entrada del dia actual
@csrf_exempt
def register_entrance_assistance(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            if data_request is None:
                return JsonResponse({
                    'title': 'Error',
                    'content': 'No data received',
                    'error': 'No data received'
                }, status=HTTPStatus.BAD_REQUEST)
            
            data = json.loads(data_request)


            student_dni = str(data.get("dni"))
            if not student_dni:
                return JsonResponse({
                    'title': 'Error',
                    'content': 'DNI not found in data',
                    'error': 'DNI not found'
                }, status=HTTPStatus.BAD_REQUEST)

            student_obj = get_or_none(Student, dni=student_dni, school__slug=slug)
            current_date = timezone.now().date()
            current_time = timezone.now().time()

            if student_obj is None:
                return JsonResponse({
                    'title': 'Estudiante no encontrado',
                    'content': 'Registre en la base de datos',
                    'error': 'Estudiante no encontrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            general_assistance = get_object_or_404(GeneralAssistance, school__slug=slug, date=current_date)

            if general_assistance.state == "Close":
                open_general_assistance(general_assistance)

            detail_assistance = get_object_or_404(DetailGeneralAssistance, general_assistance=general_assistance,
                                                  student=student_obj)

            # Si el alumno tiene una hora de entrada ya se registro
            if detail_assistance.time is not None and detail_assistance.time != "":
                return JsonResponse({
                    'title': 'Advertencia',
                    'content': 'Estudiante ya registrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            detail_assistance.time = current_time

            handle_assistance_state(detail_assistance, student_obj)

            send_whatsapp_message_to_parent(student_obj, "entrance")

            # Start WebSocket
            # Enviar actualización al dashboard en tiempo real
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"dashboard_group_{slug}",  # Usar el slug para diferenciar colegios
                {
                    "type": "send_update",
                    "general_assistance_id": general_assistance.id
                }
            )
            # End WebSocket

            return JsonResponse({'success': 'Estudiante registrado', 'image_path': student_obj.get_profile_image()},
                                status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'QR inválido',
                'error': str(e)
            }, status=HTTPStatus.BAD_REQUEST)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=HTTPStatus.METHOD_NOT_ALLOWED)

# Vista POST, recibe el json con el DNI del estudiante y lo registra a la asistencia general de salida del dia actual
@csrf_exempt
def register_exit_assistance(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)

            student_dni = str(data["dni"])
            student_obj = get_or_none(Student, dni=student_dni, school__slug=slug)
            current_date = timezone.now().date()
            current_time = timezone.now().time()

            if student_obj is None:
                return JsonResponse({
                    'title': 'Estudiante no encontrado',
                    'content': 'Registre en la base de datos',
                    'error': 'Estudiante no econtrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            detail_assistance = get_object_or_404(DetailGeneralAssistance, general_assistance__date=current_date,
                                                  student=student_obj)

            if detail_assistance.exit_time is not None and detail_assistance.exit_time != "":
                return JsonResponse({
                    'title': 'Advertencia',
                    'content': 'Estudiante ya registrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            detail_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_MARCADA
            detail_assistance.exit_time = current_time

            detail_assistance.save()

            ###########################################

            # Si el alumno no tiene una hora de entrada registrada
            if detail_assistance.time is None or detail_assistance.time == "":
                detail_assistance.time = current_time
                handle_assistance_state(detail_assistance, student_obj)

            ###########################################

            send_whatsapp_message_to_parent(student_obj, "exit")

            return JsonResponse({'success': 'Estudiante registrado', 'image_path': student_obj.get_profile_image()},
                                status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'QR inválido',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# Vista POST, recibe el json con el DNI del estudiante y lo registra a la asistencia general de entrada del dia actual (para 2 asistencias en el día)
@csrf_exempt
def register_entrance_two_assistance(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)

            student_dni = str(data["dni"])
            student_obj = get_or_none(Student, dni=student_dni, school__slug=slug)
            current_date = timezone.now().date()
            current_time = timezone.now().time()

            if student_obj is None:
                return JsonResponse({
                    'title': 'Estudiante no encontrado',
                    'content': 'Registre en la base de datos',
                    'error': 'Estudiante no econtrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            school = School.objects.get(slug=slug)

            # Primera Entrada
            if current_time < school.exit_time:
                general_assistance = get_object_or_404(GeneralAssistance, school__slug=slug, date=current_date)

                if general_assistance.state == "Close":
                    open_general_assistance(general_assistance)

                detail_assistance = get_object_or_404(DetailGeneralAssistance, general_assistance=general_assistance,
                                                      student=student_obj)

                # Si el alumno tiene una hora de entrada ya se registro
                if detail_assistance.time is not None and detail_assistance.time != "":
                    return JsonResponse({
                        'title': 'Advertencia',
                        'content': 'Estudiante ya registrado'
                    }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                detail_assistance.time = current_time

                handle_assistance_state(detail_assistance, student_obj)

                send_whatsapp_message_to_parent(student_obj, "entrance")

                # Start WebSocket
                # Enviar actualización al dashboard en tiempo real
                # channel_layer = get_channel_layer()
                # async_to_sync(channel_layer.group_send)(
                #     f"dashboard_group_{slug}",  # Usar el slug para diferenciar colegios
                #     {
                #         "type": "send_update",
                #         "general_assistance_id": general_assistance.id
                #     }
                # )
                # End WebSocket

            else:
                ## Begin Test

                detail_assistance = get_object_or_404(DetailGeneralAssistance, general_assistance__date=current_date,
                                                      student=student_obj)

                if detail_assistance.exit_time is not None and detail_assistance.exit_time != "":
                    return JsonResponse({
                        'title': 'Advertencia',
                        'content': 'Estudiante ya registrado'
                    }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                detail_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_MARCADA
                detail_assistance.exit_time = current_time

                detail_assistance.save()

                ###########################################

                # Si el alumno no tiene una hora de entrada registrada
                if detail_assistance.time is None or detail_assistance.time == "":
                    detail_assistance.time = current_time
                    handle_assistance_state(detail_assistance, student_obj)

                ###########################################

                send_whatsapp_message_to_parent(student_obj, "entrance")

                ## End Test

                # segunda entrada
                # enviar reporte de whatsapp de la segunda asistencia de entrada
                # send_whatsapp_message_to_parent(student_obj, "entrance")

            return JsonResponse({'success': 'Estudiante registrado', 'image_path': student_obj.get_profile_image()},
                                status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'QR inválido',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# Vista POST, recibe el json con el DNI del estudiante y lo registra a la asistencia general de salida del dia actual (para 2 asistencias en el día)
@csrf_exempt
def register_exit_two_assistance(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)

            student_dni = str(data["dni"])
            student_obj = get_or_none(Student, dni=student_dni, school__slug=slug)
            current_date = timezone.now().date()
            current_time = timezone.now().time()

            if student_obj is None:
                return JsonResponse({
                    'title': 'Estudiante no encontrado',
                    'content': 'Registre en la base de datos',
                    'error': 'Estudiante no econtrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            school = School.objects.get(slug=slug)

            # primera salida
            if current_time < school.entrance_time_two:
                detail_assistance = get_object_or_404(DetailGeneralAssistance, general_assistance__date=current_date,
                                                      student=student_obj)

                if detail_assistance.exit_time is not None and detail_assistance.exit_time != "":
                    return JsonResponse({
                        'title': 'Advertencia',
                        'content': 'Estudiante ya registrado'
                    }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

                detail_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_MARCADA
                detail_assistance.exit_time = current_time

                detail_assistance.save()

                ###########################################

                # Si el alumno no tiene una hora de entrada registrada
                if detail_assistance.time is None or detail_assistance.time == "":
                    detail_assistance.time = current_time
                    handle_assistance_state(detail_assistance, student_obj)

                ###########################################

                send_whatsapp_message_to_parent(student_obj, "exit")
            else:
                # segunda salida
                # enviar reporte de whatsapp de la segunda asistencia de salida
                send_whatsapp_message_to_parent(student_obj, "exit")

            return JsonResponse({'success': 'Estudiante registrado', 'image_path': student_obj.get_profile_image()},
                                status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'QR inválido',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# Vista POST, recibe el json con el DNI del estudiante y lo registra a la asistencia del estudiante al curso
@csrf_exempt
def register_course_assistance(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)
            student_dni = str(data['dni'])
            assistance_id = int(data['assistance_id'])
            current_date = timezone.now().date()
            current_time = timezone.now().time()

            assistance_obj = Assistance.objects.get(id=assistance_id)
            student_obj = get_or_none(Student, dni=student_dni, school__slug=slug)
            if student_obj is None:
                return JsonResponse({
                    'title': 'Estudiante no encontrado',
                    'content': 'Registre en la base de datos',
                    'error': 'Estudiante no econtrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            detail_assistance = assistance_obj.assistance_details.get(student=student_obj)

            if detail_assistance.time is not None and detail_assistance.time != "":
                return JsonResponse({
                    'title': 'Advertencia',
                    'content': 'Estudiante ya registrado'
                }, status=HTTPStatus.INTERNAL_SERVER_ERROR)

            detail_assistance.state = DetailAssistance.AttendanceStatus.PRESENTE
            detail_assistance.time = current_time
            detail_assistance.save()

            # Evaluando su asistencia general para colocarla
            general_assistance = get_object_or_404(GeneralAssistance, school__slug=slug, date=current_date)
            detail_general_assistance = DetailGeneralAssistance.objects.get(general_assistance=general_assistance,
                                                                            student=student_obj)
            if detail_general_assistance.time is None or detail_general_assistance.time == "":
                if general_assistance.state == "Close":
                    open_general_assistance(general_assistance)
                detail_general_assistance.time = current_time
                handle_assistance_state(detail_general_assistance, student_obj)
                send_whatsapp_message_to_parent(student_obj, "entrance", True)
                detail_general_assistance.save()

            return JsonResponse({'success': 'Estudiante registrado', 'image_path': student_obj.get_profile_image()},
                                status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'QR inválido',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# Vista POST, la cual creara la asistencia del curso cuando el profesor la haga por QR o manual
@csrf_exempt
def start_assistance_session(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)
            date = datetime.now().date()
            block_id_str = data['block']
            block_id = int(block_id_str)
            block = ScheduleBlock.objects.get(id=block_id)

            if Assistance.objects.filter(date=date, block=block).exists():
                assistance = Assistance.objects.get(date=date, block=block)
                assistance_url = reverse('assistance_app:edit_course_assistance',
                                         kwargs={'slug': slug, 'pk': assistance.id})
                return JsonResponse({'success': 'Asistencia iniciada', 'assistance_url': assistance_url}, status=200)

            assistance = Assistance.objects.create(date=date, block=block, course=block.course, state="close")

            for student in block.course.students.all():
                detail_assistance = DetailAssistance.objects.create(assistance=assistance,
                                                                    state=DetailAssistance.AttendanceStatus.DESCONOCIDO,
                                                                    student=student)

            assistance_url = reverse('assistance_app:edit_course_assistance',
                                     kwargs={'slug': slug, 'pk': assistance.id})
            return JsonResponse({'success': 'Asistencia iniciada', 'assistance_url': assistance_url}, status=200)

        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'datos no validos'}, status=400)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# Vista POST, la cual terminara la asistencia del curso, se pondra como FALTA a todos los estudiantes no registrados 
@csrf_exempt
def end_assistance_session(request, slug):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data['course']
            course = Course.objects.get(id=course_id)

            assistance = Assistance.objects.filter(course=course).latest('created')

            for student in course.students.all():
                detail_assistance = DetailAssistance.objects.get(assistance=assistance, student=student)
                if detail_assistance.state == DetailAssistance.AttendanceStatus.DESCONOCIDO:
                    detail_assistance.state = DetailAssistance.AttendanceStatus.FALTA
                    detail_assistance.save()

            return JsonResponse({'success': 'Asistencia terminada'}, status=200)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'No se pudo terminar la asistencia de manera correcta'}, status=400)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


class AddStudentsView(LoginRequiredMixin, TemplateView):
    template_name = 'director/CreateStudent.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = get_school(self.request.user)
        context['school'] = school
        ed_levels = EducationLevel.objects.filter(school=school)
        context['ed_levels'] = ed_levels
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


class AddTeachersView(LoginRequiredMixin, TemplateView):
    template_name = 'director/CreateTeacher.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = get_school(self.request.user)
        context['school'] = school
        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


class AddBlocksView(LoginRequiredMixin, TemplateView):
    template_name = 'director/CreateBlock.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')
        select_id_course = self.request.GET.get('course')

        ed_levels = school.levels.all()

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        ed_level = None
        grade = None

        if select_ed_level:
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(level=ed_level, name=select_grade)
            sections = grade.sections.all()
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().name

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(grade=grade, name=select_section)
            context['one_section'] = True
            context['section'] = section
            context['courses'] = section.course_set.all()

        if select_id_course:
            select_course = Course.objects.get(id=select_id_course)
            context['one_course'] = True
            context['course'] = select_course

        context['levels'] = ed_levels

        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


@csrf_exempt
def create_new_block(request, slug):
    if request.method == 'POST':
        data_request = request.POST.get('data')
        data = json.loads(data_request)
        course_id = int(data['course_id'])
        day = data["day"]
        time_init_str = data['time_init']
        time_end_str = data['time_end']
        time_init = datetime.strptime(time_init_str, "%H:%M").time()
        time_end = datetime.strptime(time_end_str, "%H:%M").time()
        course = Course.objects.get(id=course_id)
        new_block = ScheduleBlock.objects.create(
            course=course,
            day=day,
            time_init=time_init,
            time_end=time_end)
        return JsonResponse({'success': 'Bloque creado exitosamente'}, status=200)


class AddCourseView(LoginRequiredMixin, TemplateView):
    template_name = 'director/CreateCourse.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')

        ed_levels = school.levels.all()

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        ed_level = None
        grade = None

        if select_ed_level:
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(id=int(select_grade))
            sections = grade.sections.all()
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().id

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(id=int(select_section))
            context['one_section'] = True
            context['section'] = section

        context['levels'] = ed_levels
        context['teachers'] = school.teachers.all()

        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


@csrf_exempt
def create_new_course(request, slug):
    if request.method == 'POST':
        data_request = request.POST.get('data')
        data = json.loads(data_request)

        teacher_id = int(data['teacher_id'])
        grade_id = int(data['grade_id'])
        grade = get_object_or_404(Grade, id=grade_id)

        section_id = data['section_id']
        section = None

        if not section_id or section_id == "":
            section = grade.sections.first()
        elif section_id == "blank":
            section = None
        else:
            section = get_object_or_404(Section, id=section_id)

        teacher = get_object_or_404(Teacher, id=teacher_id)

        course_name = data['course_name']
        course_short_name = data['course_short_name']

        new_course = Course.objects.create(
            school=grade.level.school,
            name=course_name,
            short_name=course_short_name,
            teacher=teacher,
            grade=grade,
            section=section)

        return JsonResponse({'success': 'Curso creado exitosamente'}, status=200)


class SendTestMessagesView(LoginRequiredMixin, TemplateView):
    template_name = 'director/TestMessages.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        select_ed_level = self.request.GET.get('level')
        select_grade = self.request.GET.get('grade')
        select_section = self.request.GET.get('section')

        ed_levels = school.levels.all()

        if ed_levels.count() == 1:
            context['only_level'] = True
            select_ed_level = ed_levels.first().name
        elif ed_levels.count() > 1:
            context['only_level'] = False
        else:
            print("error")

        context['only_section'] = False
        context['one_level'] = False
        context['one_grade'] = False
        context['one_section'] = False
        ed_level = None
        grade = None
        if select_ed_level:
            context['one_level'] = True
            ed_level = EducationLevel.objects.get(school=school, name=select_ed_level)
            context['ed_level'] = ed_level

        if select_grade:
            grade = Grade.objects.get(level=ed_level, name=select_grade)
            sections = grade.sections.all()
            context['one_grade'] = True
            context['grade'] = grade
            if sections.count() == 1:
                context['only_section'] = True
                select_section = sections.first().name

        if select_section == "all":
            select_section = None
        if select_section:
            section = Section.objects.get(grade=grade, name=select_section)
            context['one_section'] = True
            context['section'] = section

        context['levels'] = ed_levels

        add_user_type_to_context(self.request.user, context)

        return context


# Vista POST para guardar asistencia manual
def store_manual_course_assistance(request, slug):
    if request.method == 'POST':
        current_date = timezone.now().date()
        assistance_id = int(request.POST.get('assistance_id'))
        course_assistance = get_object_or_404(Assistance, id=assistance_id)
        if course_assistance.state == "close":
            course_assistance.state = "open"
            course_assistance.save()
        students = course_assistance.block.course.students.all()
        general_assistance = get_object_or_404(GeneralAssistance, school__slug=slug, date=current_date)

        for student in students:
            student_assistance = request.POST.get(str(student.dni))
            detail_assist = course_assistance.assistance_details.all().get(student=student)

            # if detail_assist.state != student_assistance:
            #     detail_assist.time = timezone.now().time()

            if student_assistance:
                detail_assist.state = student_assistance
            else:
                detail_assist.state = "Falta"

            if detail_assist.state == DetailAssistance.AttendanceStatus.PRESENTE or detail_assist.state == DetailAssistance.AttendanceStatus.TARDANZA:
                detail_assist.time = timezone.now().time()
            else:
                detail_assist.time = None

            detail_assist.save()

            # Evaluando su asistencia general para colocarla
            if detail_assist.time is not None and detail_assist.time != "":
                detail_general_assistance = general_assistance.details_general_assistance.all().get(student=student)
                if detail_general_assistance.state == "Falta" or detail_general_assistance.state == "Desconocido":
                    if general_assistance.state == "Close":
                        open_general_assistance(general_assistance)
                        detail_general_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_NO_MARCADA
                        detail_general_assistance.save()
                    detail_general_assistance.time = timezone.now().time()
                    handle_assistance_state(detail_general_assistance, student)
                    send_whatsapp_message_to_parent(student, "entrance", True)
                    detail_general_assistance.save()

    return redirect(reverse('assistance_app:take_course_assistance', kwargs={'slug': slug}))


# def store_manual_course_assistance(request, slug):
#     if request.method == 'POST':
#         current_date = timezone.now().date()
#         assistance_id = int(request.POST.get('assistance_id'))
#         course_assistance = get_object_or_404(Assistance.objects.select_related('block__course'), id=assistance_id)
#
#         if course_assistance.state == "close":
#             course_assistance.state = "open"
#             course_assistance.save()
#
#         students = course_assistance.block.course.students.all().select_related('parent', 'school', 'grade', 'section')
#         general_assistance = get_object_or_404(
#             GeneralAssistance.objects.select_related('school'),
#             school__slug=slug,
#             date=current_date
#         )
#
#         # Cachear detalles de asistencia para evitar múltiples consultas
#         detail_assistances = {
#             da.student_id: da for da in course_assistance.assistance_details.all()
#         }
#
#         detail_general_assistances = {
#             dga.student_id: dga for dga in general_assistance.details_general_assistance.all()
#         }
#
#         with transaction.atomic():
#             for student in students:
#                 student_assistance = request.POST.get(str(student.dni))
#                 detail_assist = detail_assistances.get(student.id)
#
#                 if detail_assist and detail_assist.state != student_assistance:
#                     detail_assist.time = timezone.now().time() if student_assistance else None
#                     detail_assist.state = student_assistance if student_assistance else "Falta"
#                     detail_assist.save()
#
#                     # Evaluando su asistencia general
#                     if detail_assist.time:
#                         detail_general_assist = detail_general_assistances.get(student.id)
#
#                         if detail_general_assist.state in ["Falta", "Desconocido"]:
#                             if general_assistance.state == "Close":
#                                 open_general_assistance(general_assistance)
#                                 detail_general_assist.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_NO_MARCADA
#
#                             detail_general_assist.time = detail_assist.time
#                             handle_assistance_state(detail_general_assist, student)
#                             send_whatsapp_message_to_parent(student, "entrance", True)
#                             detail_general_assist.save()
#
#     return redirect(reverse('assistance_app:take_course_assistance', kwargs={'slug': slug}))


# Dada una seccion devuelve todos los cursos de esa seccion
def get_all_courses_from_section(section):
    courses = Course.objects.filter(section=section)
    return courses


# Cuando se crea un nuevo estudiante, se llena como desconocido a sus asistencias generales de todo el anio
def fill_general_assistances_new_student(student, gen_assistances):
    assist_list = []
    for gen_assistance in gen_assistances:
        assist_list.append(DetailGeneralAssistance(general_assistance=gen_assistance, student=student,
                                                   state=DetailGeneralAssistance.AttendanceStatus.DESCONOCIDO,
                                                   exit_state=DetailGeneralAssistance.ExitStatus.DESCONOCIDO))
    DetailGeneralAssistance.objects.bulk_create(assist_list)


# Llena como DESCONOCIDO a las asistencias de un curso de un estudiante nuevo
def fill_course_assistances_new_student(student, course):
    assist_list = []
    for assistance in course.assistances.all():
        assist_list.append(DetailAssistance(assistance=assistance, student=student,
                                            state=DetailAssistance.AttendanceStatus.DESCONOCIDO))
    DetailAssistance.objects.bulk_create(assist_list)


# Lleo como DESCONOCIDO a las asistencias de todos los cursos de un estudiante nuevo
def fill_new_student_courses_assistances(student):
    for course in student.courses.all():
        fill_course_assistances_new_student(student=student, course=course)


def validate_dni(dni):
    return bool(re.match(r'^\d{8}$', dni))


def validate_phone(phone):
    return bool(re.match(r'^\d{9}$', phone))


# test function [test]
# Vista POST para insertar estudiantes
def import_xlsx(request, slug):
    if request.method == 'POST':
        file = request.FILES['archivo_excel']
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file, dtype=str)
            school_obj = School.objects.get(slug=slug)
            ed_level = request.POST.get('level')
            level = EducationLevel.objects.get(name=ed_level, school=school_obj)
            gen_assistances = GeneralAssistance.objects.filter(school=school_obj)

            grades = {grade.short_name: grade for grade in Grade.objects.filter(level=level)}
            # sections = {section.name.upper(): section for section in Section.objects.filter(grade__level=level)}
            courses_cache = {}
            sections_grades = {}
            for grade in Grade.objects.filter(level=level):
                sections = Section.objects.filter(grade=grade)
                sections_grades[grade.short_name] = {section.name.upper(): section for section in sections}

            with transaction.atomic():
                for index, row in df.iterrows():
                    dni = str(row['dni'])
                    parent_phone1 = row.get('parent_phone1')
                    parent_phone2 = row.get('parent_phone2')
                    student_phone = row.get('student_phone')

                    if not validate_phone(str(student_phone)):
                        student_phone = ''

                    if not validate_phone(str(parent_phone1)):
                        parent_phone1 = StudentDataDefault.objects.first().phone_parent

                    if not validate_phone(str(parent_phone2)):
                        parent_phone2 = ''

                    if not validate_dni(str(dni)):
                        continue

                    grade = row['grade']
                    section_name = str(row['section']).upper()

                    if grade not in grades:
                        continue

                    grade_obj = grades[grade]
                    section_obj = sections_grades[grade][section_name]

                    if section_obj.id not in courses_cache:
                        courses_cache[section_obj.id] = get_all_courses_from_section(section_obj)

                    courses = courses_cache[section_obj.id]

                    edit_student = Student.objects.filter(dni=dni, level=level).first()

                    if edit_student:
                        edit_student.first_name = str(row.get('first_name', edit_student.first_name)).upper()
                        edit_student.last_name = str(row.get('last_name', edit_student.last_name)).upper()
                        edit_student.grade = grade_obj
                        edit_student.section = section_obj
                        edit_student.gender = str(row.get('gender', edit_student.gender)).upper()
                        edit_student.phone_number = student_phone
                        edit_student.save()

                        edit_parent = edit_student.parent
                        edit_parent.first_name = str(row.get('parent_first_name', '')).upper()
                        edit_parent.last_name = str(row.get('parent_last_name', '')).upper()
                        edit_parent.phone_number = parent_phone1
                        edit_parent.phone_number2 = parent_phone2
                        edit_parent.save()
                    else:
                        parent_first_name = str(row.get('parent_first_name', 'Sin Registro')).upper()
                        parent_last_name = str(row.get('parent_last_name', 'Sin Registro')).upper()

                        parent = Parent.objects.create(
                            phone_number=parent_phone1,
                            phone_number2=parent_phone2,
                            first_name=parent_first_name,
                            last_name=parent_last_name
                        )

                        student_obj = Student.objects.create(
                            dni=dni,
                            first_name=str(row.get('first_name')).upper(),
                            last_name=str(row.get('last_name')).upper(),
                            level=level,
                            grade=grade_obj,
                            section=section_obj,
                            school=school_obj,
                            parent=parent,
                            gender=str(row.get('gender', '')).upper(),
                            phone_number=student_phone
                        )

                        for course in courses:
                            student_obj.courses.add(course)

                        fill_general_assistances_new_student(student_obj, gen_assistances)
                        fill_new_student_courses_assistances(student_obj)

            return JsonResponse({
                'message': 'Datos importados exitosamente'
            }, status=200)
        else:
            return JsonResponse({
                'message': 'El archivo debe estar en formato Excel (.xlsx)'
            }, status=500)
    return render(request, 'student/import_xlsx.html')


def import_teacher_xlsx(request, slug):
    if request.method == 'POST':
        file = request.FILES.get('archivo_excel')
        if file and file.name.endswith('.xlsx'):
            try:
                df = pd.read_excel(file, dtype=str)
                school = School.objects.get(slug=slug)

                with transaction.atomic():
                    for index, row in df.iterrows():
                        dni = row.get('dni')
                        if not dni or not validate_dni(str(dni)):
                            continue

                        username = row.get('username')
                        email = str(row.get('email', ''))
                        first_name = str(row.get('nombre', '')).upper()
                        last_name = str(row.get('apellido', '')).upper()
                        password = str(row.get('password', '')).lower()

                        if not (username and email and first_name and last_name and password):
                            continue

                        if User.objects.filter(username=username).exists():
                            continue

                        user = User.objects.create_user(
                            username=username,
                            password=password,
                            email=email,
                            first_name=first_name,
                            last_name=last_name
                        )

                        teacher = Teacher.objects.create(
                            user=user,
                            school=school,
                            dni=dni
                        )

            except Exception as e:
                return JsonResponse({
                    'message': 'Error al importar los datos: {}'.format(str(e))
                }, status=500)

            return JsonResponse({
                'message': 'Datos importados exitosamente'
            }, status=200)
        else:
            return JsonResponse({
                'message': 'El archivo debe estar en formato Excel (.xlsx)'
            }, status=500)
    return render(request, 'student/import_xlsx.html')


def send_justification(request, slug):
    if request.method == 'POST':
        student_dni = request.POST.get('student')
        justification_type = request.POST.get('just-type')
        date_str = request.POST.get('date')
        message = request.POST.get('justification-text')

        date_object = datetime.strptime(date_str, "%Y-%m-%d").date()
        school_obj = School.objects.get(slug=slug)
        student_obj = school_obj.students.all().get(dni=student_dni)
        general_assistance = school_obj.general_assistances.all().get(date=date_object)
        detail_general_assistance = general_assistance.details_general_assistance.all().get(
            general_assistance=general_assistance,
            student=student_obj)
        if justification_type == "tardanza":
            # Si la pide antes del dia
            if detail_general_assistance.time is None or detail_general_assistance.time == "":
                detail_general_assistance.state = DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_PEDIDA
            else:
                detail_general_assistance.state = DetailGeneralAssistance.AttendanceStatus.TARDANZA_JUSTIFICADA_REGISTRADA

        elif justification_type == "falta":
            detail_general_assistance.state = DetailGeneralAssistance.AttendanceStatus.FALTA_JUSTIFICADA
            detail_general_assistance.exit_state = DetailGeneralAssistance.ExitStatus.DESCONOCIDO

        detail_general_assistance.justification = message
        detail_general_assistance.save()

        return redirect(reverse('assistance_app:justify_assistance', kwargs={'slug': slug}))

    return redirect(reverse('assistance_app:take_course_assistance', kwargs={'slug': slug}))


@csrf_exempt
def change_level_times(request, slug):
    if request.method == "POST":
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)
            level_name = data['level_name']
            new_entrance_time_str = data['new_entrance_time']
            new_exit_time_str = data['new_exit_time']
            new_tolerance_time_str = data['new_tolerance_time']

            school_obj = get_object_or_404(School, slug=slug)
            level = school_obj.levels.get(name=level_name)

            new_entrance_time = datetime.strptime(new_entrance_time_str, "%H:%M").time()
            new_exit_time = datetime.strptime(new_exit_time_str, "%H:%M").time()
            new_tolerance_time = int(new_tolerance_time_str)

            level.entrance_time = new_entrance_time
            level.exit_time = new_exit_time
            level.tolerance = new_tolerance_time

            level.save()

            return JsonResponse({'success': 'Hora cambiada exitosamente'}, status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'Datos invalidos',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


@csrf_exempt
def send_test_messages(request, slug):
    if request.method == 'POST':
        try:
            data_request = request.POST.get('data')
            data = json.loads(data_request)

            section_id_str = data["section"]
            section_id = int(section_id_str)
            section = get_object_or_404(Section, id=section_id)

            for student in section.students.all():
                send_whatsapp_message_to_parent(student, "entrance", communicated=True)

            return JsonResponse({'success': 'Mensajes enviados'}, status=200)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'title': 'Error',
                'content': 'Mensajes no enviados',
                'error': str(e)
            }, status=404)
    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)


class OtherActionsView(LoginRequiredMixin, TemplateView):
    template_name = 'director/OtherActions.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        school = get_school(self.request.user)
        context['school'] = school

        add_user_type_to_context(self.request.user, context)

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = self.request.user.id
            principal = get_or_none(Principal, user=user_id)
            if principal is None:
                return redirect('school_app:home')
        return super().dispatch(request, *args, **kwargs)


@csrf_exempt
def normalize_course_assistances(request, slug):
    if request.method == 'POST':
        school = School.objects.get(slug=slug)
        students = Student.objects.filter(school=school)

        for student in students:
            for course in student.courses.all():
                for assistance in course.assistances.all():
                    if not DetailAssistance.objects.filter(assistance=assistance, student=student).exists():
                        det_assistance = DetailAssistance.objects.create(assistance=assistance, student=student,
                                                                         state=DetailAssistance.AttendanceStatus.DESCONOCIDO)

        return JsonResponse({'success': 'Asistencias normalizadas'}, status=200)

    else:
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)
