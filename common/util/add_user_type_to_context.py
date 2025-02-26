from apps.teacher.models import Teacher
from apps.assistant.models import Auxiliar
from apps.director.models import Principal
from .get_or_none import get_or_none


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
