from modeltranslation.translator import register, TranslationOptions
from .models import (
    News, NewsBlock, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    Product, ProductFeature, ProductCardSpec, ProductParameter,
    DealerService, Dealer, BecomeADealerPage, DealerRequirement, FeatureIcon,
)


# ========== НОВОСТИ ==========
@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'desc')


@register(NewsBlock)
class NewsBlockTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


# ========== ВАКАНСИИ ==========
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


# ========== ПРОДУКТЫ ==========
@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = (
        'title',
        # Поля для слайдера
        'slider_price',
        'slider_power',
        'slider_fuel_consumption',
    )

@register(ProductFeature)
class ProductFeatureTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(ProductCardSpec)
class ProductCardSpecTranslationOptions(TranslationOptions):
    fields = ('value',)


@register(ProductParameter)
class ProductParameterTranslationOptions(TranslationOptions):
    fields = ('text',)


# ========== ДИЛЕРЫ ==========
@register(DealerService)
class DealerServiceTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Dealer)
class DealerTranslationOptions(TranslationOptions):
    fields = ('address', 'working_hours')


@register(BecomeADealerPage)
class BecomeADealerPageTranslationOptions(TranslationOptions):
    fields = ('title', 'intro_text', 'subtitle', 'important_note', 'contact_address')


@register(DealerRequirement)
class DealerRequirementTranslationOptions(TranslationOptions):
    fields = ('text',)