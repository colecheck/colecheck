from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from .models import Student, Parent
from apps.school.models import EducationLevel
from .resources import StudentResource


# Register your models here.


# class StudentAdmin(admin.ModelAdmin):
#     list_display = ('first_name', 'last_name', 'dni', 'classroom')
#
#
# admin.site.register(Student, StudentAdmin)

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('first_name', 'last_name', 'parent_phone', 'section', 'photocheck_duplicates_count')
    search_fields = ('first_name', 'last_name', 'dni', 'parent__phone_number')
    list_filter = ('school', 'level',)

    def parent_phone(self, obj):
        related_instance = getattr(obj, 'parent', None)
        if related_instance:
            return related_instance.phone_number
        else:
            return None

    def photocheck_duplicates_count(self, obj):
        return obj.photocheck_duplicates_count

    photocheck_duplicates_count.short_description = 'Cantidad de Duplicados'


@admin.register(Parent)
class ParentAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'dni', 'phone_number')
    search_fields = ('first_name', 'last_name', 'dni')
