from modeltranslation.translator import register, TranslationOptions
from .models import (
    News, 
    NewsBlock, 
    Vacancy, 
    VacancyResponsibility, 
    VacancyRequirement, 
    VacancyCondition,
    VacancyIdealCandidate,
    Product, 
    ProductFeature,
    ProductCardSpec,
    ProductParameterCategory,
    ProductParameter,
    FeatureTemplate
)

@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'desc')

@register(NewsBlock)
class NewsBlockTranslationOptions(TranslationOptions):
    fields = ('text',)

@register(Vacancy)
class VacancyTranslationOptions(TranslationOptions):
    fields = ('title', 'short_description', 'contact_info')

@register(VacancyResponsibility)
class VacancyResponsibilityTranslationOptions(TranslationOptions):
    fields = ('title', 'text')

@register(VacancyRequirement)
class VacancyRequirementTranslationOptions(TranslationOptions):
    fields = ('text',)

@register(VacancyCondition)
class VacancyConditionTranslationOptions(TranslationOptions):
    fields = ('text',)

@register(VacancyIdealCandidate)
class VacancyIdealCandidateTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('title', 'short_description', 'main_description', 'slogan', 'fuel_type', 'load_capacity')

@register(ProductFeature)
class ProductFeatureTranslationOptions(TranslationOptions):
    fields = ('name', 'value')

@register(ProductCardSpec)
class ProductCardSpecTranslationOptions(TranslationOptions):
    fields = ('value',)

@register(ProductParameterCategory)
class ProductParameterCategoryTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(ProductParameter)
class ProductParameterTranslationOptions(TranslationOptions):
    fields = ('name', 'value')

@register(FeatureTemplate)
class FeatureTemplateTranslationOptions(TranslationOptions):
    fields = ('name',)