from django.shortcuts import render


# Create your views here.
def home(request):
    # events = Event.objects.all()
    events = {}
    return render(request, "teacher/TeacherHome.html", {'events': events})


# Verificar
def check_course_assistance(request):
    return render(request, "TeacherCheckAssistance.html")


received_numbers = []


def receive_data_home(request):
    return render(request, 'teacher/showData.html', {'numbers': received_numbers})
