from modeltranslation.translator import register, TranslationOptions
from .models import (
    News, 
    NewsBlock, 
    Vacancy, 
    VacancyResponsibility, 
    VacancyRequirement, 
    VacancyCondition,
    VacancyIdealCandidate
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