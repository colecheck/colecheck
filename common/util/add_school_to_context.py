from .get_school import get_school

def add_school_to_context(user, context):
    school = get_school(user)
    context['school'] = school