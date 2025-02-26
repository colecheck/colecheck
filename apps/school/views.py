from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.core import serializers

from apps.bookstore.models import Bookstore
from apps.student.models import Student
from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from apps.school.models import School, Grade, Section

from common.util.school_slug_exists import school_slug_exists
from common.util.user_belongs_to_school import user_belongs_to_school

import json


# Create your views here.

def add_user_type_to_context(user, context):
    user_id = user.id
    if user.is_authenticated:
        is_teacher = get_or_none(Teacher, user=user_id)
        is_assistant = get_or_none(Auxiliar, user=user_id)
        is_director = get_or_none(Principal, user=user_id)

        if is_teacher is not None:
            context['teacher'] = is_teacher
        elif is_assistant is not None:
            context['assistant'] = is_assistant
        elif is_director is not None:
            context['director'] = is_director


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def get_school(user):
    if user.is_authenticated:
        user_id = user.id
        is_teacher = get_or_none(Teacher, user=user_id)
        is_assistant = get_or_none(Auxiliar, user=user_id)
        is_director = get_or_none(Principal, user=user_id)
        school = None
        if is_teacher:
            school = is_teacher.school
        if is_assistant:
            school = is_assistant.school
        if is_director:
            school = is_director.school
        return school
    return None


class HomeView(TemplateView):
    template_name_ = 'index.html'

    def get_template_names(self):
        return [self.template_name_]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_id = request.user.id
            is_teacher = get_or_none(Teacher, user=user_id)
            is_assistant = get_or_none(Auxiliar, user=user_id)
            is_director = get_or_none(Principal, user=user_id)
            is_bookstore = get_or_none(Bookstore, user=user_id)

            if is_teacher:
                school = is_teacher.school.slug
                return redirect(reverse('school_app:school_home', kwargs={'slug': school}))
            if is_assistant:
                school = is_assistant.school.slug
                return redirect(reverse('school_app:school_home', kwargs={'slug': school}))
            if is_director:
                school = is_director.school.slug
                return redirect(reverse('school_app:school_home', kwargs={'slug': school}))
            if is_bookstore:
                return redirect(reverse('school_app:generate_duplicates'))

        return super().dispatch(request, *args, **kwargs)


class SchoolHomeView(LoginRequiredMixin, TemplateView):
    template_name_ = 'index.html'
    template_name_teacher = 'teacher/TeacherHome.html'
    template_name_assistant = 'assistant/AssistantHome.html'
    template_name_director = 'director/Home.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['school'] = get_school(self.request.user)

        add_user_type_to_context(self.request.user, context)
        return context

    def get_template_names(self):
        user_id = self.request.user.id
        if self.request.user.is_authenticated:
            is_teacher = get_or_none(Teacher, user=user_id)
            is_assistant = get_or_none(Auxiliar, user=user_id)
            is_director = get_or_none(Principal, user=user_id)

            if is_teacher is not None:
                return [self.template_name_teacher]
            elif is_assistant is not None:
                return [self.template_name_assistant]
            elif is_director is not None:
                return [self.template_name_director]
        return [self.template_name_]

    def dispatch(self, request, *args, **kwargs):
        school_slug = self.kwargs.get('slug')
        if not school_slug_exists(school_slug):
            return HttpResponseNotFound("Este colegio no existe")
        if request.user.is_authenticated:
            if not user_belongs_to_school(self.request.user, **kwargs):
                return redirect('home')
        else:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


def get_levels(request):
    slug = request.GET.get('slug')
    school = School.objects.get(slug=slug)
    levels = school.levels.all()

    levels_json = serializers.serialize('json', levels)
    levels_data = json.loads(levels_json)

    return JsonResponse(levels_data, safe=False)


def get_grades(request):
    slug = request.GET.get('slug')
    level_id = request.GET.get('level_id')

    school = School.objects.get(slug=slug)
    grades = Grade.objects.filter(school=school, level_id=level_id)

    grades_json = serializers.serialize('json', grades)
    grades_data = json.loads(grades_json)

    return JsonResponse(grades_data, safe=False)


def get_sections(request):
    grade_id = request.GET.get('grade_id')

    sections = Section.objects.filter(grade_id=grade_id)

    sections_json = serializers.serialize('json', sections)
    sections_data = json.loads(sections_json)
    return JsonResponse(sections_data, safe=False)


def generate_duplicates(request):
    context = {}

    bookstore = Bookstore.objects.get(user=request.user)
    school = bookstore.school
    context['school'] = school
    context['students'] = Student.objects.filter(school=school)

    return render(request, 'bookstore/generate_duplicates.html', context)
