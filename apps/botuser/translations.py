from modeltranslation.translator import TranslationOptions, register
from .models import ReceptionMethod
from modeltranslation.admin import TranslationAdmin



@register(ReceptionMethod)
class ReceptionMethodTranslationOptions(TranslationOptions):
    fields = ('name', )
