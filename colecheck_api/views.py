from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework import generics
from rest_framework import views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

from apps.assistance.views import register_entrance_assistance, register_exit_assistance, \
    register_entrance_two_assistance, register_exit_two_assistance
from apps.student.models import Student
from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from apps.school.models import School, Course, EducationLevel, Grade, Section
from apps.assistance.models import DetailGeneralAssistance, Assistance, DetailAssistance, GeneralAssistance
from apps.teacher.views import received_numbers
from common.util.get_school import get_school
from .serializers import (
    SchoolSerializer,
    StudentSerializer,
    CourseSerializer,
    DetailGeneralAssistanceSerializer,
    GeneralAssistanceSerializer,
    EducationLevelSerializer,
    GradeSerializer,
    SectionSerializer,
    TeacherSerializer,
    AuxiliarSerializer,
    PrincipalSerializer,
    UserSerializer, NumberSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

from datetime import date, datetime, timedelta
from common.util.get_or_none import get_or_none
import requests
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
with open('secret.json') as f:
    secret = json.loads(f.read())


def get_secret(secret_name, secrets=secret):
    try:
        return secrets[secret_name]
    except Exception as e:
        message = f'La variable {secret_name} no existe [{e}]'
        raise ImproperlyConfigured(message)


class SchoolDetail(generics.RetrieveAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    lookup_field = 'slug'
    lookup_url_kwarg = 'school_slug'


class StudentList(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        school = get_object_or_404(School, slug=school_slug)
        return Student.objects.filter(school=school)


class TeacherCoursesList(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        teacher_id = self.kwargs['teacher_id']

        teacher_obj = get_object_or_404(Teacher, id=teacher_id)
        school = get_object_or_404(School, slug=school_slug)

        return school.courses.filter(teacher=teacher_obj)


class GeneralAssistanceDetailsList(generics.ListAPIView):
    serializer_class = DetailGeneralAssistanceSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        date_str = self.kwargs['date']
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        school = get_object_or_404(School, slug=school_slug)

        gen_assist_obj = school.general_assistances.get(date=date_obj)

        return gen_assist_obj.details_general_assistance.all()


class GeneralAssistancesList(generics.ListAPIView):
    serializer_class = GeneralAssistanceSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        school = get_object_or_404(School, slug=school_slug)

        return school.general_assistances.all()


class CourseStudentsList(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        course_id = self.kwargs['course_id']
        school = get_object_or_404(School, slug=school_slug)
        course_obj = school.courses.get(id=course_id)
        return course_obj.students.all()


class LevelList(generics.ListAPIView):
    serializer_class = EducationLevelSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        school = get_object_or_404(School, slug=school_slug)
        return school.levels.all()


class GradeList(generics.ListAPIView):
    serializer_class = GradeSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        level_id = self.kwargs['level_id']
        school = get_object_or_404(School, slug=school_slug)
        level_obj = school.levels.get(id=level_id)
        return level_obj.grades.all()


class SectionList(generics.ListAPIView):
    serializer_class = SectionSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']
        level_id = self.kwargs['level_id']
        grade_id = self.kwargs['grade_id']

        school = get_object_or_404(School, slug=school_slug)
        level_obj = school.levels.get(id=level_id)
        grade_obj = level_obj.grades.get(id=grade_id)
        return grade_obj.sections.all()


class TeacherList(generics.ListAPIView):
    serializer_class = TeacherSerializer

    def get_queryset(self):
        school_slug = self.kwargs['school_slug']

        school = get_object_or_404(School, slug=school_slug)
        return school.teachers.all()


def open_general_assistance(general_assistance):
    general_assistance.state = "Open"
    for detail_assistance in general_assistance.details_general_assistance.all():
        if detail_assistance.state == DetailGeneralAssistance.AttendanceStatus.DESCONOCIDO:
            detail_assistance.state = DetailGeneralAssistance.AttendanceStatus.FALTA
            detail_assistance.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_NO_MARCADA
            detail_assistance.save()


# Manejar la tardanza y si tenia justificacion
def handle_entrance_assistance_state(detail_assistance, student_obj):
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


def send_whatsapp_message_to_parent(student, attendance_type):
    time_general = datetime.now()
    time_hour = time_general.hour
    time_minute = time_general.minute
    time_second = time_general.second

    if int(time_hour) < 10:
        time_hour = f'0{time_hour}'
    if int(time_minute) < 10:
        time_minute = f'0{time_minute}'
    if int(time_second) < 10:
        time_second = f'0{time_second}'

    time = f'{time_hour}:{time_minute}:{time_second} Horas'

    """ Numero del padre de familia """
    phone_number = student.parent.phone_number
    list_of_data = [f'{student.first_name}',
                    f'{student.last_name}', f'{time}']
    ngrok_url = get_secret('NGROK_HOST')
    url = f'{ngrok_url}/asistencia'
    # Datos JSON que deseas enviar
    data = {
        'time_assistance': f'{time_hour}:{time_minute}:{time_second}',
        'student': f'{student.first_name}, {student.last_name}',
        'phone_number': f'{phone_number}',
        'type_assistance': f'{attendance_type}'
    }
    # Convierte los datos a formato JSON
    json_data = json.dumps(data)
    # Encabezados de la solicitud
    headers = {'Content-Type': 'application/json'}
    # Realiza la solicitud POST
    response = requests.post(url, data=json_data, headers=headers)
    # sendWhastAppMessage(phone_number, list_of_data)
    print("*******************************************************")
    print(response)
    print("*******************************************************")


class RegisterEntranceGeneralAssistance(views.APIView):
    def post(self, request, *args, **kwargs):
        school_slug = kwargs.get('school_slug')
        student_dni = request.data.get('dni')

        current_time = timezone.now().time()
        current_date = timezone.now().date()

        school = get_object_or_404(School, slug=school_slug)

        student = get_or_none(Student, dni=student_dni, school=school)
        if student is None:
            response_data = {
                'title': 'Estudiante no encontrado',
                'content': 'Registre en la base de datos',
                'error': 'Estudiante no econtrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        general_assistance = school.general_assistances.get(date=current_date)

        if general_assistance == "Close":
            open_general_assistance(general_assistance)

        detail_ga = general_assistance.details_general_assistance.get(student=student)

        if detail_ga.time is not None and detail_ga.time != "":
            response_data = {
                'title': 'Advertencia',
                'content': 'Estudiante ya registrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        detail_ga.time = current_time

        handle_entrance_assistance_state(detail_ga, student)

        send_whatsapp_message_to_parent(student, "entrance")
        response_data = {
            'success': 'Estudiante registrado',
            'image_path': student.get_profile_image()
        }
        return Response(response_data, status=status.HTTP_200_OK)


class RegisterExitGeneralAssistance(views.APIView):
    def post(self, request, *args, **kwargs):
        school_slug = kwargs.get('school_slug')
        student_dni = request.data.get('dni')

        current_time = timezone.now().time()
        current_date = timezone.now().date()

        school = get_object_or_404(School, slug=school_slug)

        student = get_or_none(Student, dni=student_dni, school=school)
        if student is None:
            response_data = {
                'title': 'Estudiante no encontrado',
                'content': 'Registre en la base de datos',
                'error': 'Estudiante no econtrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        general_assistance = school.general_assistances.get(date=current_date)

        if general_assistance == "Close":
            open_general_assistance(general_assistance)

        detail_ga = general_assistance.details_general_assistance.get(student=student)

        if detail_ga.exit_time is not None and detail_ga.exit_time != "":
            response_data = {
                'title': 'Advertencia',
                'content': 'Estudiante ya registrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        detail_ga.exit_time = current_time
        detail_ga.exit_state = DetailGeneralAssistance.ExitStatus.SALIDA_MARCADA

        detail_ga.save()

        send_whatsapp_message_to_parent(student, "exit")

        response_data = {
            'success': 'Estudiante registrado',
            'image_path': student.get_profile_image()
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RegisterCourseAssistance(views.APIView):
    def post(self, request, *args, **kwargs):
        school_slug = kwargs.get('school_slug')
        student_dni = request.data.get('dni')
        assistance_id = request.data.get('assistance_id')

        current_date = timezone.now().date()
        current_time = timezone.now().time()

        assistance_obj = get_object_or_404(Assistance, id=assistance_id)
        student_obj = get_or_none(Student, dni=student_dni, school__slug=school_slug)

        if student_obj is None:
            response_data = {
                'title': 'Estudiante no encontrado',
                'content': 'Registre en la base de datos',
                'error': 'Estudiante no econtrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        detail_assistance = assistance_obj.assistance_details.get(student=student_obj)

        if detail_assistance.time is not None and detail_assistance.time != "":
            response_data = {
                'title': 'Advertencia',
                'content': 'Estudiante ya registrado'
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        detail_assistance.state = DetailAssistance.AttendanceStatus.PRESENTE
        detail_assistance.time = current_time
        detail_assistance.save()

        general_assistance = get_object_or_404(GeneralAssistance, school__slug=school_slug, date=current_date)
        detail_general_assistance = DetailGeneralAssistance.objects.get(general_assistance=general_assistance,
                                                                        student=student_obj)
        if detail_general_assistance.time is None or detail_general_assistance.time == "":
            if general_assistance.state == "Close":
                general_assistance.state = "Open"
                general_assistance.save()
                open_general_assistance(general_assistance)
            detail_general_assistance.time = current_time
            handle_entrance_assistance_state(detail_general_assistance, student_obj)
            send_whatsapp_message_to_parent(student_obj, "entrance")
            detail_general_assistance.save()

        response_data = {
            'success': 'Estudiante registrado',
            'image_path': student_obj.get_profile_image()
        }

        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendJustification(views.APIView):
    def post(self, request, *args, **kwargs):
        student_dni = request.data.get()


class ChangeLevelTimes(views.APIView):
    def post(self, request, *args, **kwargs):
        school_slug = kwargs.get('school_slug')
        level_name = request.data.get('level_name')
        new_entrance_time_str = request.data.get('new_entrance_time')
        new_exit_time_str = request.data.get('new_exit_time')
        new_tolerance_time_str = request.data.get('new_tolerance_time')

        school_obj = get_object_or_404(School, slug=school_slug)
        level = school_obj.levels.get(name=level_name)

        new_entrance_time = datetime.strptime(new_entrance_time_str, "%H:%M").time()
        new_exit_time = datetime.strptime(new_exit_time_str, "%H:%M").time()
        new_tolerance_time = int(new_tolerance_time_str)

        level.entrance_time = new_entrance_time
        level.exit_time = new_exit_time
        level.tolerance = new_tolerance_time

        level.save()

        response_data = {
            'success': 'Hora cambiada exitosamente'
        }

        return Response(response_data, status=status.HTTP_200_OK)


class CurrentUserDetail(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_id = user.id

        is_teacher = get_or_none(Teacher, user=user_id)
        is_assistant = get_or_none(Auxiliar, user=user_id)
        is_director = get_or_none(Principal, user=user_id)

        serializer = None

        if is_teacher is not None:
            serializer = TeacherSerializer(is_teacher)
        elif is_assistant is not None:
            serializer = AuxiliarSerializer(is_assistant)
        elif is_director is not None:
            serializer = PrincipalSerializer(is_director)
        if serializer is not None:
            return Response(serializer.data)

        return Response({'error': 'Error fatal ha ocurrido'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlacklistTokenUpdateView(views.APIView):
    permissions_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])

    if not user.check_password(request.data['password']):
        return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

    is_assistant = get_or_none(Auxiliar, user=user)

    if is_assistant is None:
        return Response({"error": "Usuario no autorizado"}, status=status.HTTP_401_UNAUTHORIZED)

    school = get_school(user=user)

    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)
    school_serializer = SchoolSerializer(instance=school)

    return Response({
        'token': token.key,
        'user': serializer.data,
        'school': school_serializer.data
    }, status=status.HTTP_200_OK)


def invertir_dni(dni):
    dni_invertido = dni[::-1]
    return dni_invertido


def desplazamiento_izquierda(dni, posiciones):
    dni_desplazado = dni[posiciones:] + dni[:posiciones]
    return dni_desplazado


def decifrar_dni(dni_cifrado):
    dni_invertido = desplazamiento_izquierda(dni_cifrado, -3)
    dni_descifrado = invertir_dni(dni_invertido)
    return dni_descifrado


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def register_assistance(request):
    try:
        data = request.data
        dni = data.get('dni')
        type_assistance = data.get("type_assistance")

        if not dni or not type_assistance:
            return Response({"error": "Datos incompletos"}, status=status.HTTP_400_BAD_REQUEST)

        school = request.user.auxiliar.school
        slug = school.slug

        # dni_descifrado = decifrar_dni(dni)

        fake_request = HttpRequest()
        fake_request.method = 'POST'
        # fake_request.POST['data'] = json.dumps({"dni": dni_descifrado})

        if not school.is_double_turn:
            dni_descifrado = decifrar_dni(dni)
            fake_request.POST['data'] = json.dumps({"dni": dni_descifrado})
            if type_assistance == "entrance":
                response = register_entrance_assistance(fake_request, slug)
                if response.status_code != 200:
                    return Response({
                        "error": "Alumno no encontrado"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif type_assistance == "exit":
                response = register_exit_assistance(fake_request, slug)
                if response.status_code != 200:
                    return Response({
                        "error": "Alumno no encontrado"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Tipo de Asistencia Invalido"
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            fake_request.POST['data'] = json.dumps({"dni": dni})
            if type_assistance == "entrance":
                response = register_entrance_two_assistance(fake_request, slug)
                if response.status_code != 200:
                    return Response({
                        "error": "Alumno no encontrado"
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif type_assistance == "exit":
                response = register_exit_two_assistance(fake_request, slug)
                if response.status_code != 200:
                    return Response({
                        "error": "Alumno no encontrado"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Tipo de Asistencia Invalido"
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": "Alumno registrado",
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# test hardware
@api_view(['POST'])
def receive_data(request):
    serializer = NumberSerializer(data=request.data)
    if serializer.is_valid():
        number = serializer.validated_data['number']
        received_numbers.append(number)
        if len(received_numbers) > 20:
            received_numbers.clear()
        return Response({'status': 'success', 'number': number})
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_info_school(request):
    try:
        school = request.user.auxiliar.school
        levels = EducationLevel.objects.filter(school=school)
        school_structure = {}

        for level in levels:
            grades = Grade.objects.filter(level=level)
            grades_dict = {}

            for grade in grades:
                sections = Section.objects.filter(grade=grade)
                sections_list = list(sections.values('id', 'name'))
                grades_dict[grade.name] = {
                    'id': grade.id,
                    'sections': sections_list
                }

            school_structure[level.name] = {
                'id': level.id,
                'grades': grades_dict
            }

        return Response(school_structure, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_students_info(request):
    try:
        data = request.data
        level_id = data.get('level_id')
        grade_id = data.get('grade_id')
        section_id = data.get('section_id')

        if not level_id or not grade_id or not section_id:
            return Response({'error': 'Los campos level_id, grade_id y section_id son requeridos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        school = request.user.auxiliar.school

        # Filtrar el nivel
        level = EducationLevel.objects.filter(id=level_id, school=school).first()
        if not level:
            return Response({'error': 'Nivel no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Filtrar el grado
        grade = Grade.objects.filter(id=grade_id, level=level).first()
        if not grade:
            return Response({'error': 'Grado no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Filtrar la sección
        section = Section.objects.filter(id=section_id, grade=grade).first()
        if not section:
            return Response({'error': 'Sección no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Filtrar los estudiantes
        students = Student.objects.filter(section=section)
        students_list = list(students.values('id', 'first_name', 'last_name', 'dni'))

        response_data = {
            'level': {
                'id': level.id,
                'name': level.name
            },
            'grade': {
                'id': grade.id,
                'name': grade.name
            },
            'section': {
                'id': section.id,
                'name': section.name
            },
            'students': students_list
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
