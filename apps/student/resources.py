from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Student, Parent


class StudentResource(resources.ModelResource):
    dni = fields.Field(attribute='dni', column_name='dni')
    first_name = fields.Field(attribute='first_name', column_name='first_name')
    last_name = fields.Field(attribute='last_name', column_name='last_name')
    grade = fields.Field(attribute='grade__short_name', column_name='grade')
    section = fields.Field(attribute='section__short_name', column_name='section')
    gender = fields.Field(attribute='gender', column_name='gender')
    student_phone = fields.Field(attribute='phone_number', column_name='student_phone')
    parent_first_name = fields.Field(attribute='parent__first_name', column_name='parent_first_name')
    parent_last_name = fields.Field(attribute='parent__last_name', column_name='parent_last_name')
    parent_phone1 = fields.Field(attribute='parent__phone_number', column_name='parent_phone1')
    parent_phone2 = fields.Field(attribute='parent__phone_number2', column_name='parent_phone2')
    whatsapp_phone = fields.Field(attribute='parent__whatsapp_phone', column_name='whatsapp_phone')
    whatsapp_phone2 = fields.Field(attribute='parent__whatsapp_phone2', column_name='whatsapp_phone2')

    class Meta:
        model = Student
        fields = ('dni', 'first_name', 'last_name', 'grade', 'section', 'gender', 'student_phone',
                  'parent_first_name', 'parent_last_name', 'parent_phone1', 'parent_phone2', 'whatsapp_phone',
                  'whatsapp_phone2')
        export_order = ('dni', 'first_name', 'last_name', 'grade', 'section', 'gender', 'student_phone',
                        'parent_first_name', 'parent_last_name', 'parent_phone1', 'parent_phone2', 'whatsapp_phone',
                        'whatsapp_phone2')
