from django.db import models
from django.contrib.auth.models import User

from apps.school.models import School


# Create your models here.
class Bookstore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario", related_name="bookstore")
    school = models.ForeignKey(School, verbose_name='Colegio', related_name='bookstore', on_delete=models.CASCADE, null=True, blank=True)
    dni = models.CharField('DNI', max_length=8, blank=True, null=True)
    profile_image = models.ImageField('Foto Perfil', upload_to='profile_image/', null=True, blank=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        verbose_name = 'Librería'
        verbose_name_plural = 'Librerías'
