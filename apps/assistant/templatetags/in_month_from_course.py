from django import template
from apps.school.models import Course
register = template.Library()

@register.filter
def one_more(_1, _2):
    return _1, _2

@register.filter
def in_month_from_course(_1_2, course_id):
    assistances, month = _1_2
    course = int(course_id)
    course_obj = Course.objects.get(id=course)
    return assistances.filter(assistance__date__month=int(month), assistance__course=course_obj)

@register.filter
def from_course(assistances, course_id):
    course = int(course_id)
    course_obj = Course.objects.get(id=course)
    return assistances.filter(assistance__course=course_obj)


