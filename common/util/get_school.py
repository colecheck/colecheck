from .get_or_none import get_or_none
from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from apps.bookstore.models import Bookstore


def get_school(user):
    if user.is_authenticated:
        user_id = user.id
        is_teacher = get_or_none(Teacher, user=user_id)
        is_assistant = get_or_none(Auxiliar, user=user_id)
        is_director = get_or_none(Principal, user=user_id)
        is_bookstore = get_or_none(Bookstore, user=user_id)

        school = None
        if is_teacher:
            school = is_teacher.school
        if is_assistant:
            school = is_assistant.school
        if is_director:
            school = is_director.school
        if is_bookstore:
            school = is_bookstore.school
        return school
    return None
