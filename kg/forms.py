from django import forms
from django.core.files.base import ContentFile
from .models import VehicleCardSpec, IconTemplate
import uuid
import os


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
                print(f"✅ Найден шаблон иконки ID={template_id}: {template.name}")
                
                # Удаляем старую иконку если есть
                if instance.icon:
                    try:
                        old_path = instance.icon.path
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            print(f"🗑️ Удалена старая иконка: {old_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось удалить старую иконку: {e}")
                
                # Копируем новую иконку
                filename = f"spec_{uuid.uuid4().hex[:8]}_{os.path.basename(template.icon.name)}"
                
                with template.icon.open('rb') as icon_file:
                    file_content = icon_file.read()
                    instance.icon.save(
                        filename,
                        ContentFile(file_content),
                        save=False
                    )
                    print(f"💾 Сохранена новая иконка: {filename}")
                    
            except IconTemplate.DoesNotExist:
                print(f"❌ Шаблон иконки ID={template_id} не найден")
            except Exception as e:
                print(f"❌ Ошибка при копировании иконки: {e}")
        
        if commit:
            instance.save()
        
        return instance