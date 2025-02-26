from django.db import models
from ..student.models import Student


# Create your models here.
class Assistance(models.Model):
    
    date = models.DateField(auto_now_add=False)
    course = models.ForeignKey('school.Course', verbose_name="Curso", on_delete=models.CASCADE, blank=True, null=True, related_name="assistances")
    block = models.ForeignKey('school.ScheduleBlock', verbose_name="Bloque", on_delete=models.SET_NULL, related_name="assistances", blank=True, null=True)
    state = models.CharField('Estado', max_length=20, default="close", blank=True, null=True)
    #code_generation = models.CharField('Codigo unico', max_length=250, unique=True)

    def get_day(self):
        return self.date.strftime('%d')
    
    def __str__(self):
        return f'{self.date}/{self.block}'

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['course', 'date']


class DetailAssistance(models.Model):
    assistance = models.ForeignKey(Assistance, verbose_name='Asistencia', related_name='assistance_details',
                                   on_delete=models.CASCADE, null=True, blank=True)
    time = models.TimeField(auto_now_add=False, verbose_name='Hora', null=True)
    student = models.ForeignKey(Student, verbose_name='Estudiante', related_name='assistances',
                                on_delete=models.CASCADE, null=True, blank=True)

    class AttendanceStatus(models.TextChoices):
        PRESENTE = "Presente"
        FALTA = "Falta"
        TARDANZA = "Tardanza"
        PERMISO = "Permiso"
        DESCONOCIDO = "Desconocido"

    state = models.CharField(
        max_length=40,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENTE
    )
    def __str__(self):
        return f'{self.assistance.date}/{self.time}/{self.student.first_name}'

    class Meta:
        verbose_name = 'Detalle de Asistencia'
        verbose_name_plural = 'Detalle de Asistencias'

        ordering = ['assistance']

class GeneralAssistance(models.Model):
    date = models.DateField(auto_now_add=False, verbose_name='Fecha')
    school = models.ForeignKey('school.School', verbose_name='Colegio', related_name='general_assistances', on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField('Estado', max_length=20, default="Close", blank=True, null=True)
    def __str__(self):
        return f'{self.date}'

    class Meta:
        verbose_name = "Asistencia General"
        verbose_name_plural = "Asistencias Generales"
        ordering = ['date']


# Asistencia general al momento de la entrada y la salida del colegio
class DetailGeneralAssistance(models.Model):
    general_assistance = models.ForeignKey(GeneralAssistance, verbose_name='Asistencia General', related_name='details_general_assistance',
                                           on_delete=models.CASCADE, null=False)
    time = models.TimeField(auto_now_add=False, verbose_name='Hora', null=True)
    student = models.ForeignKey(Student, verbose_name='Estudiante', related_name='general_assistances',
                                on_delete=models.CASCADE, null=True, blank=True)
    justification = models.TextField(verbose_name="Justificacion", null=True, blank=True)
    
    class AttendanceStatus(models.TextChoices):
        PRESENTE = "Presente"
        TARDANZA = "Tardanza"
        TARDANZA_JUSTIFICADA_PEDIDA = "Tardanza Justificada Pedida"
        TARDANZA_JUSTIFICADA_REGISTRADA = "Tardanza Justificada Registrada"
        FALTA = "Falta"
        FALTA_JUSTIFICADA = "Falta Justificada"
        DESCONOCIDO = "Desconocido"

    state = models.CharField(
        max_length=40,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENTE
    )

    # La toma de asistencia a la salida es manejada por este valor, que se pondra como SALIDA_NO_MARCADA cuando se tome la asistencia de entrada
    # Cuando se tome la asistencia de salida se marcara como SALIDA_CORRECTA

    # Despues del momento de una tolerancia a la hora de entrada, automaticamente se podria enviar un prompt para anadir las asistencias de los demas estudiantes como falta

    class ExitStatus(models.TextChoices):
        SALIDA_MARCADA = "Salio"
        SALIDA_NO_MARCADA = "Aun no salio"
        DESCONOCIDO = "Desconocido"

    exit_state = models.CharField(
        max_length=20,
        choices=ExitStatus.choices,
        default=ExitStatus.SALIDA_NO_MARCADA
    )

    exit_time = models.TimeField(auto_now_add=False, verbose_name='Hora de Salida', blank=True, null=True)
        
    def __str__(self):
        return f'Asistencia de {self.student.last_name}'
    
    class Meta:
        verbose_name = 'Detalles de Asistencia General'
        verbose_name_plural = "Detalles de Asistencias Generales"

        ordering = ['general_assistance']

