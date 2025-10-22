from django import forms
from django.core.files.base import ContentFile
from .models import VehicleCardSpec, IconTemplate
import uuid
import os
import logging
logger = logging.getLogger(__name__)


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
            
                # Копируем новую иконку
                filename = f"spec_{uuid.uuid4().hex[:8]}_{os.path.basename(template.icon.name)}"
                
                with template.icon.open('rb') as icon_file:
                    file_content = icon_file.read()
                    instance.icon.save(
                        filename,
                        ContentFile(file_content),
                        save=False
                    )

                        
            except IconTemplate.DoesNotExist:
                logger.error(f"Шаблон иконки ID={template_id} не найден")
            except Exception as e:
                logger.error(f"Ошибка при копировании иконки: {e}")
        
        if commit:
            instance.save()
        
        return instance