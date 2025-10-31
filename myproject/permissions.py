from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def setup_permissions():
    """Создание групп с правами доступа для FAW"""
    
    # 1. ГЛАВНЫЕ АДМИНЫ
    main_admins, created = Group.objects.get_or_create(name='Главные админы')
    if created:
        all_permissions = Permission.objects.filter(
            content_type__app_label__in=['main', 'kg']
        )
        main_admins.permissions.set(all_permissions)
        
        user_permissions = Permission.objects.filter(
            Q(content_type__app_label='auth') &
            ~Q(codename='delete_user')
        )
        main_admins.permissions.add(*user_permissions)
    
    # 2. КОНТЕНТ-АДМИНЫ
    content_admins, created = Group.objects.get_or_create(name='Контент-админы')
    if created:
        content_models = [
            'news', 'newsblock', 'product', 'productparameter',
            'productfeature', 'productgallery', 'productcardspec',
            'vacancy', 'vacancyresponsibility', 'vacancyrequirement',
            'vacancycondition', 'vacancyidealcandidate',
            'dealer', 'dealerservice', 'featureicon',
            'becomeadealerpage', 'dealerrequirement'
        ]
        
        content_permissions = Permission.objects.filter(
            content_type__model__in=content_models,
            content_type__app_label='main'
        ).exclude(codename__startswith='delete_')
        
        content_admins.permissions.set(content_permissions)
    
    # 3. ЛИД-МЕНЕДЖЕРЫ
    lead_managers, created = Group.objects.get_or_create(name='Лид-менеджеры')
    if created:
        lead_models = ['contactform', 'jobapplication', 'becomeadealer application']
        
        lead_permissions = Permission.objects.filter(
            content_type__model__in=[m.replace(' ', '') for m in lead_models],
            content_type__app_label='main'
        ).exclude(codename__startswith='delete_')
        
        lead_managers.permissions.set(lead_permissions)