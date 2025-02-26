from django.contrib import admin
from .models import NgrokConfiguration, StudentDataDefault, Contact


# Register your models here.

class NgrokConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "host",)
    list_editable = ("host",)


admin.site.register(NgrokConfiguration, NgrokConfigurationAdmin)


class StudentDataDefaultAdmin(admin.ModelAdmin):
    list_display = ("id", "phone_parent")
    list_editable = ("phone_parent",)


admin.site.register(StudentDataDefault, StudentDataDefaultAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'subject', 'created_at')
    search_fields = ('name', 'phone', 'email', 'subject', 'message')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    fields = ('name', 'email', 'subject', 'message', 'created_at', 'honeypot')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Personalizar el queryset aquí si es necesario
        return queryset

    def save_model(self, request, obj, form, change):
        # Agregar lógica adicional al guardar el modelo
        super().save_model(request, obj, form, change)


admin.site.register(Contact, ContactAdmin)
