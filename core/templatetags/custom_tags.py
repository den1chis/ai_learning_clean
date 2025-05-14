
from django import template

register = template.Library()
from core.models import UserAnswer

@register.filter
def question_attempts(question, user):
    return UserAnswer.objects.filter(user=user, question=question).count()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def prev_lesson_id(lessons, index):
    try:
        if index > 0:
            return lessons[index - 1].id
    except:
        return None

@register.filter
def prev_lesson_index(lessons, index):
    """Возвращает предыдущий урок по индексу"""
    try:
        return lessons[index - 1] if index > 0 else None
    except IndexError:
        return None

@register.filter
def getattr_dynamic(obj, attr):
    return getattr(obj, attr, '')
@register.filter
def question_attempts(question, user):
    return UserAnswer.objects.filter(user=user, question=question).count()