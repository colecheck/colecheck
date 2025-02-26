import json
from collections import defaultdict

import pandas as pd
import re
import requests

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from apps.school.models import School, Section
from apps.student.models import Student
from apps.system.forms import ContactForm
from apps.system.models import NgrokConfiguration

from django.utils.timezone import now


# Create your views here.

class HomeView(TemplateView):
    template_name = 'system/homeView.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        schools = School.objects.all()
        school_data = []

        select_date = now().date()

        for school in schools:
            try:
                general_assistance = school.general_assistances.get(date=select_date)
                details = general_assistance.details_general_assistance.all()

                attendance_data = details.aggregate(
                    Presente=Count('state', filter=Q(state='Presente')),
                    Tardanza=Count('state', filter=Q(state='Tardanza')),
                    Falta=Count('state', filter=Q(state='Falta'))
                )

                attendance_data_json = json.dumps(attendance_data)

                school_data.append({
                    'school_name': school.name,
                    'attendance_data': attendance_data_json
                })

            except school.general_assistances.model.DoesNotExist:
                school_data.append({
                    'school_name': school.name,
                    'attendance_data': json.dumps({'Presente': 0, 'Tardanza': 0, 'Falta': 0})
                })

        context['school_data'] = school_data
        context['schools'] = schools
        context['select_date'] = select_date

        return context


class StudentListView(ListView):
    model = Student
    template_name = 'system/studentList.html'
    context_object_name = 'students'
    paginate_by = 10  # Número de estudiantes por página

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def validate_dni(dni):
    return bool(re.match(r'^\d{8}$', dni))


def validate_phone(phone):
    return bool(re.match(r'^\d{9}$', phone))


def update_status_whatsapp_students(request):
    if request.method == 'POST':
        try:
            file = request.FILES['excelFile']
            if not file.name.endswith('.xlsx'):
                return JsonResponse({
                    'message': 'El archivo debe estar en formato Excel (.xlsx)'
                }, status=500)

            df = pd.read_excel(file, dtype=str)

            with transaction.atomic():
                for index, row in df.iterrows():
                    dni = str(row['dni'])

                    if not validate_dni(str(dni)):
                        return JsonResponse({
                            'message': f'Error: DNI incorrecto: {dni}'
                        }, status=500)

                    parent_phone1 = row.get('parent_phone1')
                    have_whatsapp = row.get('whatsapp_phone')

                    parent_phone2 = row.get('parent_phone2')
                    have_whatsapp2 = row.get('whatsapp_phone2')

                    if not validate_phone(str(parent_phone1)):
                        parent_phone1 = ''

                    if not validate_phone(str(parent_phone2)):
                        parent_phone2 = ''

                    try:
                        current_student_obj = Student.objects.get(dni=dni)
                        parent_student_obj = current_student_obj.parent

                        if parent_student_obj.phone_number != parent_phone1:
                            return JsonResponse({
                                'message': f'Error: No se encontró coincidencia para el estudiante con DNI {dni}'
                            }, status=500)

                        if parent_student_obj.phone_number2 != parent_phone2:
                            return JsonResponse({
                                'message': f'Error: No se encontró coincidencia para el estudiante con DNI {dni}'
                            }, status=500)

                        parent_student_obj.whatsapp_phone = str(have_whatsapp).lower() == 'true'
                        parent_student_obj.whatsapp_phone2 = str(have_whatsapp2).lower() == 'true'

                        parent_student_obj.save()
                        current_student_obj.save()

                    except Student.DoesNotExist:
                        return JsonResponse({
                            'message': f'Error: No se encontró estudiante con DNI {dni}'
                        }, status=500)

            return JsonResponse({
                'message': 'Datos importados exitosamente'
            }, status=200)

        except Exception as e:
            return JsonResponse({
                'message': f'Error al procesar el archivo: {str(e)}'
            }, status=500)

    return render(request, 'system/studentList.html')


def download_students_data(request):
    queryset = Student.objects.all()

    data = {
        'dni': [student.dni for student in queryset],
        'parent_phone1': [student.parent.phone_number for student in queryset],
        'parent_phone2': [student.parent.phone_number2 for student in queryset],
        'whatsapp_phone': [student.parent.whatsapp_phone for student in queryset],
        'whatsapp_phone2': [student.parent.whatsapp_phone2 for student in queryset],
    }
    df = pd.DataFrame(data)

    file_name = 'students_data.xlsx'
    excel_file = df.to_excel(file_name, index=False)

    excel_data = open(file_name, 'rb').read()
    response = HttpResponse(excel_data,
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={file_name}'

    return response


@csrf_protect
@ratelimit(key='ip', rate='2/m', method='POST', block=True)
def send_contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        honeypot = request.POST.get('honeypot', '')
        if honeypot:
            return JsonResponse({'message': 'Spam detectado'}, status=400)

        try:
            if form.is_valid():
                contact = form.save()
                return JsonResponse({'message': 'Mensaje enviado con éxito'}, status=200)
            else:
                return JsonResponse({'message': form.errors.as_json()}, status=400)
        except ValidationError as e:
            return JsonResponse({'message': str(e)}, status=400)
        except Ratelimited:
            return JsonResponse({'message': 'Límite de envío superado, inténtelo de nuevo más tarde.'}, status=429)

    return render(request, 'index.html', {'form': ContactForm()})


def get_weekly_attendance_report(section_id=None, school=None):
    if school:
        students = Student.objects.filter(school=school).prefetch_related('details_general_assistance')
    elif section_id:
        students = Student.objects.filter(section_id=section_id).prefetch_related('details_general_assistance')
        school = Section.objects.get(id=section_id).grade.school

    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)

    assistances = school.general_assistances.filter(date__range=(monday, friday), state='Open')

    attendance_data_by_student = defaultdict(lambda: {
        'nombre_completo': '',
        'lunes': '------',
        'martes': '------',
        'miercoles': '------',
        'jueves': '------',
        'viernes': '------',
        'estado': '',
        'nro_faltas': 0,
        'nro_tardanzas': 0,
        'nro_temprano': 0,
        'porcentaje_asistencia': 0,
    })

    day_map = {
        0: 'lunes',
        1: 'martes',
        2: 'miercoles',
        3: 'jueves',
        4: 'viernes',
    }

    for assistance in assistances:
        assistance_day = day_map[assistance.date.weekday()]
        for detail in assistance.details_general_assistance.filter(student__in=students):
            # student_name = f"{detail.student.first_name} {detail.student.last_name}"
            # student_name = f'{detail.student}'

            student = detail.student
            dni = student.dni
            full_name = f'{student.first_name} {student.last_name}'

            # Asigna los datos básicos del estudiante
            attendance_data_by_student[dni]['nombre_completo'] = full_name

            # Asignar el estado de asistencia en el día correspondiente
            if detail.state == 'Presente':
                attendance_data_by_student[dni][assistance_day] = 'Temprano'
                attendance_data_by_student[dni]['nro_temprano'] += 1
            elif 'Tardanza' in detail.state:
                attendance_data_by_student[dni][assistance_day] = 'Tardanza'
                attendance_data_by_student[dni]['nro_tardanzas'] += 1
            elif 'Falta' in detail.state:
                attendance_data_by_student[dni][assistance_day] = 'Falta'
                attendance_data_by_student[dni]['nro_faltas'] += 1

        # Si la asistencia está cerrada y el estudiante no tiene un estado registrado, marcar "Sin asistencia"
        # if assistance.state == 'Close':
        #     for student in students:
        #         student_name = f"{student.first_name} {student.last_name}"
        #         if attendance_data_by_student[student_name][assistance_day] == 'Sin asistencia':
        #             attendance_data_by_student[student_name][assistance_day] = 'Sin asistencia'

    total_attendance_days = len(assistances)  # Numero de días que se tomo asistencia

    # Calcular el porcentaje de asistencia y clasificar el estado
    for student_name, data in attendance_data_by_student.items():
        total_attendance = data['nro_temprano'] + data['nro_tardanzas']
        # total_dias = len(assistances)  # Numero de días que se tomo asistencia
        # data['total_attendance_days'] = total_dias

        if total_attendance_days > 0:
            data['porcentaje_asistencia'] = (total_attendance / total_attendance_days) * 100

            # Clasificar según el porcentaje de asistencia
            if data['porcentaje_asistencia'] > 80:
                data['estado'] = 'Alto'
            elif data['porcentaje_asistencia'] > 50:
                data['estado'] = 'Medio'
            else:
                data['estado'] = 'Bajo'

    return attendance_data_by_student, total_attendance_days


@csrf_exempt
def get_school_report_week(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido',
        }, status=405)

    data_request = request.POST.get('data')
    data = json.loads(data_request)
    slug = data["slug"]

    school = School.objects.get(slug=slug)
    attendance_data_by_student, total_attendance_days = get_weekly_attendance_report(section_id=None, school=school)

    return JsonResponse({
        'status': 'success',
        'message': 'Resumen de asistencia generado exitosamente',
        'data': attendance_data_by_student,
        'total_attendance_days': total_attendance_days
    })


def send_whatsapp_message_to_parent(student, attendance_type, in_classroom=False, communicated=False, student_data=None,
                                    date_range=None, type_report=None):
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
        'communicated': communicated_msg,
        'data': student_data,
        'date_range': date_range,
        'type_report': type_report
    }

    json_data = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    url = f'{ngrok_url}/asistencia-reporte'
    requests.post(url, data=json_data, headers=headers)


@csrf_exempt
def send_school_report_week(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido',
        }, status=405)

    data_request = request.POST.get('data')
    data = json.loads(data_request)

    # ************************************************ #
    # slug = data["slug"]
    # school = School.objects.get(slug=slug)
    # attendance_data_by_student, total_attendance_days = get_weekly_attendance_report(school)
    # ************************************************ #
    section_id = data["sectionId"]
    attendance_data_by_student, total_attendance_days = get_weekly_attendance_report(section_id=section_id, school=None)
    # ************************************************ #

    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    date_range = f"{monday.strftime('%d')} - {friday.strftime('%d %b')}"

    for student_dni, student_data in attendance_data_by_student.items():
        try:
            student = Student.objects.get(dni=student_dni)
            send_whatsapp_message_to_parent(student, "Entrada", communicated=True, student_data=student_data,
                                            date_range=date_range, type_report=0)
        except Student.DoesNotExist:
            continue

    return JsonResponse({
        'status': 'success',
        'message': 'Resumen de asistencia generado y mensajes enviados exitosamente',
        'section': str(Section.objects.get(id=section_id)),
        'data': attendance_data_by_student
    })

def get_monthly_attendance_report(section_id=None, school=None, month=None):
    if not school and not section_id:
        raise ValueError("Debe proporcionar un parámetro válido: 'section_id' o 'school'.")

    month = int(month)
    if not month or month < 1 or month > 12:
        raise ValueError("Debe proporcionar un mes válido (1-12).")

    if school:
        students = Student.objects.filter(school=school).prefetch_related('details_general_assistance')
    elif section_id:
        students = Student.objects.filter(section_id=section_id).prefetch_related('details_general_assistance')
        school = Section.objects.get(id=section_id).grade.school

    first_day = datetime(datetime.today().year, month, 1)
    last_day = first_day + relativedelta(months=1) - timedelta(days=1)

    assistances = school.general_assistances.filter(
        date__range=(first_day, last_day),
        state='Open'
    )

    attendance_data_by_student = defaultdict(lambda: {
        'nombre_completo': '',
        'nro_temprano': 0,
        'nro_tardanzas': 0,
        'nro_faltas': 0,
        'porcentaje_asistencia': 0,
    })

    total_attendance_days = len(assistances)  # Número total de días con asistencia en el mes
    total_students = students.count()
    total_attendance_by_school = 0

    for assistance in assistances:
        for detail in assistance.details_general_assistance.filter(student__in=students):
            student = detail.student
            dni = student.dni
            full_name = f'{student.first_name} {student.last_name}'

            attendance_data_by_student[dni]['nombre_completo'] = full_name

            if detail.state == 'Presente':
                attendance_data_by_student[dni]['nro_temprano'] += 1
            elif 'Tardanza' in detail.state:
                attendance_data_by_student[dni]['nro_tardanzas'] += 1
            elif 'Falta' in detail.state:
                attendance_data_by_student[dni]['nro_faltas'] += 1

    # Calcular porcentajes de asistencia por estudiante
    for data in attendance_data_by_student.values():
        total_attendance = data['nro_temprano'] + data['nro_tardanzas']
        if total_attendance_days > 0:
            data['porcentaje_asistencia'] = (total_attendance / total_attendance_days) * 100
            total_attendance_by_school += data['porcentaje_asistencia']

    # Calcular promedio de asistencia en el colegio
    school_average_attendance = 0
    if total_students > 0:
        school_average_attendance = total_attendance_by_school / total_students

    # Agregar el promedio al reporte
    for data in attendance_data_by_student.values():
        data['promedio_colegio'] = school_average_attendance

    return {
        "attendance_report": attendance_data_by_student,
        "total_attendance_days": total_attendance_days,
        "school_average_attendance": school_average_attendance,
    }


@csrf_exempt
def send_school_report_month(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido',
        }, status=405)

    data_request = request.POST.get('data')
    data = json.loads(data_request)

    # ************************************************ #
    # slug = data["slug"]
    # school = School.objects.get(slug=slug)
    # attendance_data_by_student, total_attendance_days = get_weekly_attendance_report(school)
    # ************************************************ #
    section_id = data["sectionId"]
    month = data["month"]
    report_data = get_monthly_attendance_report(section_id=section_id, school=None, month=month)
    attendance_data_by_student = report_data['attendance_report']
    total_attendance_days = report_data['total_attendance_days']
    school_average_attendance = report_data['school_average_attendance']
    # ************************************************ #

    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    date_range = month

    for student_dni, student_data in attendance_data_by_student.items():
        try:
            student = Student.objects.get(dni=student_dni)
            send_whatsapp_message_to_parent(student, "Entrada", communicated=True, student_data=student_data,
                                            date_range=date_range, type_report=1)
        except Student.DoesNotExist:
            continue

    return JsonResponse({
        'status': 'success',
        'message': 'Resumen de asistencia generado y mensajes enviados exitosamente',
        'section': str(Section.objects.get(id=section_id)),
        'data': attendance_data_by_student
    })

