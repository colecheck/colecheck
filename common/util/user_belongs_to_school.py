from .get_school import get_school
from apps.school.models import School


def user_belongs_to_school(user, **kwargs):
    if user.is_authenticated:
        user_school = get_school(user)
        url_school_slug = kwargs['slug']
        url_school = School.objects.get(slug=url_school_slug)

        return user_school == url_school
    return False
