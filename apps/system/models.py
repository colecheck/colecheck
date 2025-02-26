from django.db import models

# Create your models here.
class NgrokConfiguration(models.Model):
    host = models.URLField(max_length=255)

    def __str__(self):
        return self.host

    class Meta:
        verbose_name = "Ngrok Configuracion"
        verbose_name_plural = "Ngrok Configuraciones"


class StudentDataDefault(models.Model):
    phone_parent = models.CharField('WhatsApp Defecto', max_length=9, blank=True, null=True)

    def __str__(self) -> str:
        return self.phone_parent
    
    class Meta:
        verbose_name = 'Dato de Estudiante por Defecto'
        verbose_name_plural = 'Datos de Estudiante por Defecto'


class Contact(models.Model):
    name = models.CharField(verbose_name='Nombre', max_length=100)
    phone = models.CharField(verbose_name='Teléfono', max_length=20)
    email = models.EmailField(verbose_name='Email')
    subject = models.CharField(verbose_name='Asunto', max_length=100)
    message = models.TextField(verbose_name='Asunto')
    created_at = models.DateTimeField(verbose_name='Creado', auto_now_add=True)
    honeypot = models.CharField(verbose_name='Honeypot', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Email Contacto'
        verbose_name_plural = 'Emails de Contactos'

    def __str__(self):
        return self.name