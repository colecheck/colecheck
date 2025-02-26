from django import template

register = template.Library()

@register.filter
def in_month(assistances, month):
    return assistances.filter(general_assistance__date__month=int(month))