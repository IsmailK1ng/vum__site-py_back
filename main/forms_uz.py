from django import forms
from django.core.files.base import ContentFile
from .models import ProductFeature, ProductCardSpec, FeatureTemplate
import uuid
import os


class ProductFeatureForm(forms.ModelForm):
    """Форма для характеристик с выбором иконки из шаблонов"""
    selected_template = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'selected-template-field'})
    )
    
    class Meta:
        model = ProductFeature
        fields = ['product', 'icon', 'name', 'value', 'order', 'selected_template']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        template_id = self.cleaned_data.get('selected_template')
        
        if template_id:
            try:
                template = FeatureTemplate.objects.get(id=template_id)
                
                # Удаляем старую иконку
                if instance.icon:
                    try:
                        old_path = instance.icon.path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except:
                        pass
                
                # Копируем иконку из шаблона
                filename = f"feature_{uuid.uuid4().hex[:8]}_{os.path.basename(template.icon.name)}"
                
                with template.icon.open('rb') as icon_file:
                    instance.icon.save(
                        filename,
                        ContentFile(icon_file.read()),
                        save=False
                    )
                    
                # Автоматически заполняем название из шаблона
                if not instance.name:
                    instance.name = template.name
                    
            except FeatureTemplate.DoesNotExist:
                pass
        
        if commit:
            instance.save()
        
        return instance


class ProductCardSpecForm(forms.ModelForm):
    """Форма для характеристик карточки с выбором иконки"""
    selected_template = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'selected-template-field'})
    )
    
    class Meta:
        model = ProductCardSpec
        fields = ['product', 'icon', 'value', 'order', 'selected_template']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        template_id = self.cleaned_data.get('selected_template')
        
        if template_id:
            try:
                template = FeatureTemplate.objects.get(id=template_id)
                
                if instance.icon:
                    try:
                        old_path = instance.icon.path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except:
                        pass
                
                filename = f"card_{uuid.uuid4().hex[:8]}_{os.path.basename(template.icon.name)}"
                
                with template.icon.open('rb') as icon_file:
                    instance.icon.save(
                        filename,
                        ContentFile(icon_file.read()),
                        save=False
                    )
                    
            except FeatureTemplate.DoesNotExist:
                pass
        
        if commit:
            instance.save()
        
        return instance