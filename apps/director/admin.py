from django.contrib import admin
from .models import Principal

class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'school', 'dni')
    list_filter = ('school',)
    search_fields = ('user__first_name', 'user__last_name', 'dni')

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Nombre completo'

admin.site.register(Principal, PrincipalAdmin)
