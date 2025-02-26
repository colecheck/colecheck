from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from datetime import date, datetime, timedelta
from datetime import timedelta
from apps.assistance.models import GeneralAssistance, Assistance, DetailAssistance
import os
from django.utils import timezone

from apps.student.models import Student


class School(models.Model):
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField(unique=True, blank=True, default="")
    entrance_time = models.TimeField(auto_now_add=False, verbose_name="Hora de Entrada")
    exit_time = models.TimeField(auto_now_add=False, verbose_name="Hora de Salida")
    slogan = models.CharField(verbose_name="Eslogan", max_length=255, null=True, blank=True)
    primary_color = models.CharField(max_length=30, verbose_name="Color primario", null=True, blank=True)
    secondary_color = models.CharField(max_length=30, verbose_name="Color secundario", null=True, blank=True)
    logo = models.ImageField('Logo', upload_to='school_logo/', null=True, blank=True)
    communicated = models.TextField(verbose_name="Comunicados", null=True, blank=True)

    department = models.CharField(verbose_name="Departamento", null=True, blank=True, max_length=100)
    province = models.CharField(verbose_name="Provincia", null=True, blank=True, max_length=100)
    district = models.CharField(verbose_name="Distrito", null=True, blank=True, max_length=100)

    is_double_turn = models.BooleanField(verbose_name="Doble Turno", default=False)
    entrance_time_two = models.TimeField(auto_now_add=False, verbose_name="Hora de Entrada 2", null=True, blank=True)
    exit_time_two = models.TimeField(auto_now_add=False, verbose_name="Hora de Salida 2", null=True, blank=True)

    fotocheck_template_front = models.ImageField(upload_to='fotocheck_template/', null=True, blank=True)
    fotocheck_template_back = models.ImageField(upload_to='fotocheck_template/', null=True, blank=True)

    use_card = models.BooleanField(verbose_name="Usa tarjeta", default=False, null=True, blank=True)

    # Creando las asistencias generales cuando se cree el colegio
    def generate_general_assistances_dates(self):
        actual_year = date.today().year
        start_date = date(actual_year, 1, 1)
        end_date = date(actual_year, 12, 31)
        delta = timedelta(days=1)

        while start_date <= end_date:
            new_assistance, created = GeneralAssistance.objects.get_or_create(date=start_date, school=self)
            start_date += delta

    # Si se guarda sin slug definido, lo define automaticamente
    def save(self, *args, **kwargs):
        is_created = self.pk is None
        if not self.slug:
            self.slug = slugify(self.name)
        super(School, self).save(*args, **kwargs)

        if is_created:
            self.generate_general_assistances_dates()

    def get_logo(self):
        if not self.logo:
            return f'/static/img/profile_default.webp'
        return self.logo.url

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Colegio'
        verbose_name_plural = 'Colegios'

        ordering = ["name"]


class EducationLevel(models.Model):
    school = models.ForeignKey(School, verbose_name='Colegio', on_delete=models.SET_NULL, related_name='levels',
                               null=True, blank=True)
    name = models.CharField('Nombre', max_length=30)
    entrance_time = models.TimeField(auto_now_add=False, verbose_name="Hora de Entrada", default='08:00', blank=True,
                                     null=True)
    exit_time = models.TimeField(auto_now_add=False, verbose_name="Hora de Salida", default='13:00', blank=True,
                                 null=True)
    tolerance = models.IntegerField('Tolerancia de Entrada', default=0)

    def __str__(self):
        return f'{self.school.slug}/{self.name}'

    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"

        ordering = ['school']


class Grade(models.Model):
    school = models.ForeignKey(School, verbose_name="Colegio", on_delete=models.SET_NULL, related_name='grades',
                               null=True, blank=True)
    level = models.ForeignKey(EducationLevel, verbose_name='Nivel', on_delete=models.SET_NULL, related_name='grades',
                              null=True, blank=True)  # Para que me deje migrar
    name = models.CharField('Nombre', max_length=20)
    short_name = models.CharField('Abreviatura', max_length=5)

    def __str__(self):
        return f'{self.level.school.slug}/{self.level.name}/{self.short_name}'

    class Meta:
        verbose_name = 'Grado'
        verbose_name_plural = 'Grados'

        ordering = ['level', 'short_name']


class Section(models.Model):
    grade = models.ForeignKey(Grade, verbose_name='Grado', on_delete=models.CASCADE, related_name='sections')
    name = models.CharField('Nombre', max_length=20)  # e. g Sec-5-A
    short_name = models.CharField('Abreviatura', max_length=3, null=True, blank=True)  # e.g. A

    def __str__(self):
        return f'{self.grade.level.school.slug}/{self.grade.level.name}/{self.grade.short_name}/{self.name}'

    class Meta:
        verbose_name = 'Seccion'
        verbose_name_plural = 'Secciones'

        ordering = ['grade', 'name']


##### APUNTA DE ELIMINAR ###########

class Classroom(models.Model):
    grade = models.ForeignKey(Grade, verbose_name='Grado', on_delete=models.CASCADE)
    section = models.CharField('Seccion', max_length=3)

    def __str__(self):
        return f'{self.grade.short_name} - {self.section}'

    class Meta:
        verbose_name = 'Aula'
        verbose_name_plural = 'Aulas'


########################################


class Course(models.Model):
    school = models.ForeignKey(School, verbose_name='Colegio', related_name='courses', on_delete=models.SET_NULL,
                               null=True, blank=True)
    name = models.CharField('Nombre curso', max_length=50)
    short_name = models.CharField('Abreviatura', max_length=10)
    teacher = models.ForeignKey('teacher.Teacher', verbose_name='Profesor', related_name='courses',
                                on_delete=models.SET_NULL, null=True)
    grade = models.ForeignKey(Grade, verbose_name="Grado", related_name='courses', on_delete=models.SET_NULL, null=True,
                              blank=True)
    section = models.ForeignKey(Section, verbose_name="Seccion", related_name='course_set', on_delete=models.SET_NULL,
                                null=True, blank=True)

    def __str__(self):
        if self.section:
            return f'{self.school.slug}/{self.name}/{self.grade.level.name}/{self.grade.short_name}/{self.section.name}'
        return f'{self.school.slug}/{self.name}/{self.grade.level.name}/{self.grade.short_name}'

    def save(self, *args, **kwargs):
        super(Course, self).save(*args, **kwargs)
        if self.section is not None and self.section != "":
            for student in self.section.students.all():
                student.courses.add(self)
                student.save()

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['section', 'name']


class ScheduleBlock(models.Model):
    course = models.ForeignKey(Course, verbose_name='Curso', related_name='blocks', on_delete=models.CASCADE)

    class DayOfTheWeek(models.TextChoices):
        LUNES = "Lunes"
        MARTES = "Martes"
        MIERCOLES = "Miercoles"
        JUEVES = "Jueves"
        VIERNES = "Viernes"
        SABADO = "Sabado"
        DOMINGO = "Domingo"

    day = models.CharField(
        'Dia',
        max_length=20,
        choices=DayOfTheWeek.choices,
        default=DayOfTheWeek.LUNES
    )

    time_init = models.TimeField('Hora inicio', default="08:00")
    time_end = models.TimeField('Hora Fin', default="13:00")

    class ScheduleBlockStatus(models.TextChoices):
        ACTIVE = "active"
        INACTIVE = "inactive"

    status = models.CharField(
        'Estado',
        max_length=30,
        choices=ScheduleBlockStatus.choices,
        default=ScheduleBlockStatus.ACTIVE
    )

    def __str__(self):
        if self.course.section:
            return f'{self.course.name} - {self.day} {self.time_init} - {self.course.grade.level.school.slug}/{self.course.grade.level.name}/{self.course.grade.short_name}/{self.course.section.name}'
        return f'{self.course.name} - {self.day} {self.time_init} - {self.course.grade.level.school.slug}/{self.course.grade.level.name}/{self.course.grade.short_name}'

    def int_from_weekday(self, weekday):
        days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        return days.index(weekday)

    def create_assistances_for_year(self):
        current_year = timezone.now().date().year
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
        current_date = start_date
        assist_list = []
        while current_date <= end_date:
            if current_date.weekday() == self.int_from_weekday(self.day):
                assist_list.append(Assistance(date=current_date, block=self, course=self.course, state="close"))
            current_date += timedelta(days=1)
        Assistance.objects.bulk_create(assist_list)

    def save(self, *args, **kwargs):
        super(ScheduleBlock, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Bloque de Horario'
        verbose_name_plural = 'Bloques de Horario'
        ordering = ['course', 'day', 'time_init', 'time_end']


class PhotocheckDuplicates(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario",
                             related_name='photocheck_duplicates')
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name="Colegio",
                               related_name='photocheck_duplicates')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Estudiante",
                                related_name='photocheck_duplicates')
    datetime = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    is_paid = models.BooleanField(default=False, verbose_name="¿Pagado?")
    amount = models.DecimalField(max_digits=5, verbose_name="Monto", decimal_places=2,
                                 validators=[MinValueValidator(0.00)])

    def __str__(self):
        return self.student.get_fullname()

    class Meta:
        verbose_name = 'Duplicado Fotocheck'
        verbose_name_plural = 'Duplicados Fotocheck'
