from modeltranslation.translator import TranslationOptions, register
from .models import Product, ProductCategory, ProductColor, ProductTaste, ProductVolume
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

@register(ProductCategory)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(ProductColor)
class ProductTranslationOptions(TranslationOptions):
    fields = ('color',)



@register(ProductTaste)
class ProductTranslationOptions(TranslationOptions):
    fields = ('taste',)

@register(ProductVolume)
class ProductTranslationOptions(TranslationOptions):
    fields = ('volume',)



@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('product_name', "description")
