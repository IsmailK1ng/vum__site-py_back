
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import News, Product, PageMeta

# ========== SIGNAL ДЛЯ НОВОСТЕЙ ==========

@receiver(post_save, sender=News)
def create_seo_for_news(sender, instance, created, **kwargs):
 
    if created:
 
        PageMeta.objects.get_or_create(
            model='Post',  
            key=str(instance.id),
            
         
            defaults={
                'is_active': False,  
                'title': '',  
                'description': '',  
                'keywords': '', 
                'og_type': 'article',  
            }
        )
        
# ========== SIGNAL ДЛЯ ПРОДУКТОВ ==========

@receiver(post_save, sender=Product)
def create_seo_for_product(sender, instance, created, **kwargs):
    """
    Автоматически создает SEO запись при создании продукта.
    
    Работает точно так же как для новостей!
    """
    
    if created:
        PageMeta.objects.get_or_create(
            model='Product',  
            key=str(instance.id),  
            
            defaults={
                'is_active': False,  
                'title': '',
                'description': '',
                'keywords': '',
                'og_type': 'product', 
            }
        )

