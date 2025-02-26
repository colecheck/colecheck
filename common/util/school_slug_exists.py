from apps.school.models import School
from .get_or_none import get_or_none


def school_slug_exists(school_slug):
    school_obj = get_or_none(School, slug=school_slug)
    if school_obj:
        return True
    return False
