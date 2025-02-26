from django.core.management.base import BaseCommand
from apps.student.models import Student, Parent
import pandas as pd


class Command(BaseCommand):
    help = 'Process a file'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='The name of the file to process')

    def handle(self, *args, **options):
        filename = options['filename']
        df = pd.read_excel(filename)

        for index, row in df.iterrows():
            dni = str(row['dni'])
            phone_number = row['phone_number']

            student_obj = Student.objects.get(dni=dni)
            parent_obj = student_obj.parent
            parent_obj.phone_number = phone_number
            parent_obj.save()
