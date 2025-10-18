from modeltranslation.translator import register, TranslationOptions
from .models import (
    News, NewsBlock, ContactForm, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    Product, ProductFeature, ProductSpecification, SpecificationCategory
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


@register(SpecificationCategory)
class SpecificationCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'short_description',
        'main_description',
        'slogan',
    )


@register(ProductFeature)
class ProductFeatureTranslationOptions(TranslationOptions):
    fields = ('name', 'value')


@register(ProductSpecification)
class ProductSpecificationTranslationOptions(TranslationOptions):
    fields = ('name', 'value')