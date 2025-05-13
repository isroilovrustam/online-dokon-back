from modeltranslation.translator import TranslationOptions, register
from .models import Shop, ShopAddress
from modeltranslation.admin import TranslationAdmin


class CustomAdmin(TranslationAdmin):
    class Media:
        js = (
            'https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }
@register(Shop)
class ShopTranslationOptions(TranslationOptions):
    fields = ("shop_name", "description", )

@register(ShopAddress)
class ShopTranslationOptions(TranslationOptions):
    fields = ("full_address", )