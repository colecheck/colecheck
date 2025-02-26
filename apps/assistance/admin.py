from django.contrib import admin
from .models import Assistance, DetailAssistance, GeneralAssistance, DetailGeneralAssistance


# Register your models here.



def set_to_close(modeladmin, request, queryset):
    queryset.update(state="close")

class AssistanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'block', 'id')
    actions = [set_to_close]

admin.site.register(Assistance, AssistanceAdmin)


def reset_assistances(modeladmin, request, queryset):
    queryset.update(state="Desconocido", time=None)


class DetailAssistanceAdmin(admin.ModelAdmin):
    list_display = ('assistance', 'time', 'student', 'state')
    list_filter = ('assistance__date', 'assistance__course__school')
    actions = [reset_assistances]


admin.site.register(DetailAssistance, DetailAssistanceAdmin)


def set_state_to_unknown(modeladmin, request, queryset):
    queryset.update(state="Desconocido", exit_state="Desconocido", time=None, exit_time=None)

set_state_to_unknown.short_description = "Resetear asistencia"

class DetailGeneralAssistanceAdmin(admin.ModelAdmin):
    list_display = ('time', 'general_assistance', 'student', 'state')
    # Filtrar por fecha de DetailAssistance
    list_filter = ('general_assistance__date', 'general_assistance__school')
    list_editable = ('state',)
    actions = [set_state_to_unknown]


admin.site.register(DetailGeneralAssistance, DetailGeneralAssistanceAdmin)


def set_state_to_close(modeladmin, request, queryset):
    queryset.update(state="Close")

set_state_to_close.short_description = "Cerrar asistencias"

class GeneralAssistanceAdmin(admin.ModelAdmin):
    actions = [set_state_to_close]
    list_filter = ('date', 'school')

admin.site.register(GeneralAssistance, GeneralAssistanceAdmin)
