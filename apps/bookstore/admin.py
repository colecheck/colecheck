from django.contrib import admin
from .models import Bookstore


# Register your models here.

@admin.register(Bookstore)
class BookstoreAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'school', 'dni')
    search_fields = ('user__first_name', 'user__last_name', 'dni', 'school__name')
    list_filter = ('school',)
    fields = ('user', 'school', 'dni', 'profile_image')

    def user_full_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'

    user_full_name.short_description = 'Nombre Completo'
