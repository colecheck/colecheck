import pandas as pd

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.school.models import Classroom, Grade, Section
from apps.student.models import Student

from django.http import JsonResponse


# Create your views here.
class GenerateQrView(TemplateView):
    template_name = 'student/generate_qr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        students = Student.objects.all()
        classrooms = Classroom.objects.all()

        context['students'] = students
        context['classrooms'] = classrooms

        return context


def home(request):
    # events = Event.objects.all()
    events = {}
    return render(request, "student/StudentHome.html", {'home': events})


def assistance(request):
    return render(request, "student/StudentAssistance.html")


def schedule(request):
    return render(request, "student/StudentSchedule.html")
