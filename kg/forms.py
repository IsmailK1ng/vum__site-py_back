from django import forms
from django.core.files.base import ContentFile
from django.conf import settings
from .models import VehicleCardSpec, IconTemplate
import uuid
import os
import shutil


class VehicleCardSpecForm(forms.ModelForm):
    selected_template = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'selected-template-field'})
    )
    
    class Meta:
        model = VehicleCardSpec
        fields = ['vehicle', 'icon', 'value_ru', 'value_ky', 'value_en', 'order', 'selected_template']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        template_id = self.cleaned_data.get('selected_template')
        
        if template_id:
            try:
                template = IconTemplate.objects.get(id=template_id)
                
                # Удаляем старую иконку
                if instance.pk and instance.icon:
                    instance.icon.delete(save=False)
                
                # Генерируем имя файла
                filename = f"spec_{uuid.uuid4().hex[:8]}_{os.path.basename(template.icon.name)}"
                
                
                source_path = template.icon.path
                dest_path = os.path.join(settings.MEDIA_ROOT, 'kg_vehicles/card_icons', filename)
                
                # Создаём папку если нет
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Копируем файл
                shutil.copy2(source_path, dest_path)
                
                # Сохраняем путь в БД
                instance.icon.name = f'kg_vehicles/card_icons/{filename}'
                        
            except Exception as e:
                pass
        
        if commit:
            instance.save()
        
        return instance