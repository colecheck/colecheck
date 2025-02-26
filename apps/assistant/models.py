from django.db import models
from django.contrib.auth.models import User
from apps.school.models import School


class Auxiliar(models.Model):

    user = models.OneToOneField(User, verbose_name='Usuario', related_name='auxiliar', on_delete=models.CASCADE)
    school = models.ForeignKey(School, verbose_name='Colegio', related_name='assistants', on_delete=models.CASCADE, null=True, blank=True)
    dni = models.CharField('DNI', max_length=8, blank=True, null=True)
    profile_image = models.ImageField('Foto Perfil', upload_to ='profile_image/', null=True, blank=True)
    
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    class Meta:
        verbose_name = 'Auxiliar'
        verbose_name_plural = 'Auxiliares'