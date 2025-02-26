from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.core.files import File

from PIL import Image
from io import BytesIO

from .models import Student


@receiver(post_delete, sender=Student)
def delete_parent_with_student(sender, instance, **kwargs):
    if instance.parent:
        instance.parent.delete()


def optimize_image(image):
    img = Image.open(image)
    img = img.convert('RGB')
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    return File(output, name=image.name)


@receiver(pre_save, sender=Student)
def pre_save_image_optimization(sender, instance, **kwargs):
    if instance.profile_image:
        instance.profile_image = optimize_image(instance.profile_image)