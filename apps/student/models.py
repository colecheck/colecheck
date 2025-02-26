from typing import Iterable
from django.db import models
from django.utils.deconstruct import deconstructible

import os


@deconstructible
class PathAndRename:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{instance.dni}.{ext}'
        return os.path.join(self.path, instance.school.slug, filename)


profile_image_upload_path = PathAndRename('profile_image')


class Parent(models.Model):
    first_name = models.CharField('Nombre', max_length=50, null=True, blank=True)
    last_name = models.CharField('Apellido', max_length=50, null=True, blank=True)
    dni = models.CharField('DNI', unique=True, max_length=8, null=True, blank=True)
    phone_number = models.CharField('Numero de Telefono', max_length=12)
    whatsapp_phone = models.BooleanField(default=False, blank=True, null=True)

    phone_number2 = models.CharField('Segundo numero de telefono', max_length=12, null=True, blank=True)
    whatsapp_phone2 = models.BooleanField(default=False, blank=True, null=True)

    def get_fullname(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Padre de Familia'
        verbose_name_plural = 'Padres de Familia'

        ordering = ['last_name']


class Student(models.Model):
    first_name = models.CharField('Nombre', max_length=50)
    last_name = models.CharField('Apellido', max_length=50)
    dni = models.CharField('DNI', max_length=8, unique=True)
    gender = models.CharField("Genero", max_length=10, null=True, blank=True)
    school = models.ForeignKey('school.School', verbose_name='Colegio',
                               related_name='students', on_delete=models.CASCADE, null=True, blank=True)
    profile_image = models.ImageField('Foto Perfil', upload_to=profile_image_upload_path, null=True, blank=True)
    level = models.ForeignKey('school.EducationLevel', verbose_name='Nivel de educacion', on_delete=models.SET_NULL,
                              null=True, blank=True)
    grade = models.ForeignKey('school.Grade', verbose_name='Grado', on_delete=models.SET_NULL, related_name='students',
                              null=True, blank=True)
    section = models.ForeignKey('school.Section', verbose_name="Seccion", on_delete=models.SET_NULL,
                                related_name='students',
                                null=True, blank=True)

    parent = models.OneToOneField(
        Parent, verbose_name='Padre de Familia', on_delete=models.PROTECT, related_name='student')

    # Debido a casos excepcionales como en talleres de EPT,
    # los estudiantes tienen su propia relacion con el curso,
    # mas alla de su respectiva clase que se encuentren
    courses = models.ManyToManyField(
        'school.Course', verbose_name='Cursos', related_name='students', blank=True)
    phone_number = models.CharField(
        'Numero de telefono', max_length=15, blank=True, null=True)

    def get_fullname(self):
        return f'{self.first_name} {self.last_name}'

    def get_profile_image(self):
        if not self.profile_image:
            return f'/static/img/avatar_profile.png'
        return self.profile_image.url

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'level': self.level.name,
            'grade': self.grade.name,
            'section': self.section.name,
            # 'school': self.school.name
            # adicionalmente slogan del colegio
        }

    def save(self, *args, **kwargs):
        is_created = self.pk is None
        super(Student, self).save(*args, **kwargs)
        if is_created:
            for course in self.section.course_set.all():
                self.courses.add(course)

    @property
    def photocheck_duplicates_count(self):
        return self.photocheck_duplicates.count()

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

        ordering = ['school', 'grade', 'section', 'last_name']
