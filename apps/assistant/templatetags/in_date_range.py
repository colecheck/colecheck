from django import template
from datetime import datetime
register = template.Library()

@register.filter
def one_more(_1, _2):
    return _1, _2

@register.filter
def in_date_range(_1_2, end_date):
    assistances, start_date = _1_2
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    return assistances.filter(general_assistance__date__gte=start_date_obj, general_assistance__date__lte=end_date_obj)
