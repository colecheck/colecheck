from django.contrib import admin
from .models import Course, School, EducationLevel, Grade, Section, ScheduleBlock, PhotocheckDuplicates


class SchoolFilter(admin.SimpleListFilter):
    title = 'Colegio'
    parameter_name = 'school'

    def lookups(self, request, model_admin):
        return School.objects.values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(course__school_id=self.value())


class LevelFilter(admin.SimpleListFilter):
    title = 'Nivel'
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        return EducationLevel.objects.filter(school_id=request.GET.get('school')).values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(course__grade__level_id=self.value())


class GradeFilter(admin.SimpleListFilter):
    title = 'Grado'
    parameter_name = 'grade'

    def lookups(self, request, model_admin):
        return Grade.objects.filter(level_id=request.GET.get('level')).values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(course__grade_id=self.value())


class SectionFilter(admin.SimpleListFilter):
    title = 'Sección'
    parameter_name = 'section'

    def lookups(self, request, model_admin):
        return Section.objects.filter(grade_id=request.GET.get('grade')).values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(course__section_id=self.value())


class ScheduleBlockAdmin(admin.ModelAdmin):
    list_display = ('course', 'day', 'time_init', 'time_end', 'status')
    list_editable = ("status",)
    list_filter = (SchoolFilter, LevelFilter, GradeFilter, SectionFilter, 'day', 'status')


admin.site.register(ScheduleBlock, ScheduleBlockAdmin)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'teacher', 'grade', 'section')
    list_filter = ('school', 'grade__level', 'grade', 'teacher',)


admin.site.register(Course, CourseAdmin)


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'communicated')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('communicated',)


admin.site.register(School, SchoolAdmin)


class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)


admin.site.register(EducationLevel, EducationLevelAdmin)


class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'level')
    list_filter = ('school', 'level')


admin.site.register(Grade, GradeAdmin)


class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade')
    list_filter = ('grade__school', 'grade')


admin.site.register(Section, SectionAdmin)


class PhotocheckDuplicatesAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'user', 'datetime', 'is_paid', 'amount')
    readonly_fields = ('amount', 'datetime')
    list_filter = ('is_paid', 'datetime', 'school')
    search_fields = ('user__username', 'student__dni', 'school__name', 'student__first_name')
    list_editable = ('is_paid',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'school', 'student')
        return self.readonly_fields


admin.site.register(PhotocheckDuplicates, PhotocheckDuplicatesAdmin)
