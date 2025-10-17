from django import forms
from django.core.files.base import ContentFile
from .models import VehicleCardSpec, IconTemplate


class VehicleCardSpecForm(forms.ModelForm):
    """Форма с обработкой выбранной иконки"""
    
    # Добавляем скрытое поле для ID шаблона
    selected_template = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = VehicleCardSpec
        fields = ['vehicle', 'value_ru', 'value_ky', 'value_en', 'order', 'selected_template']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        print(f"\n🔍 ФОРМА СОХРАНЯЕТСЯ: {self.prefix}")
        print(f"  value_ru: {instance.value_ru}")
        print(f"  cleaned_data: {self.cleaned_data}")
        
        # Получаем ID выбранного шаблона
        template_id = self.cleaned_data.get('selected_template')
        
        if template_id:
            try:
                template = IconTemplate.objects.get(id=template_id)
                print(f"  ✅ Найден шаблон: {template.name} (ID: {template.id})")
                
                # Удаляем старую иконку
                if instance.icon:
                    try:
                        instance.icon.delete(save=False)
                        print(f"  🗑️ Старая иконка удалена")
                    except Exception as e:
                        print(f"  ⚠️ Ошибка удаления старой иконки: {e}")
                
                # Копируем новую
                import uuid
                filename = f"spec_{uuid.uuid4().hex[:8]}_{template.icon.name.split('/')[-1]}"
                
                with template.icon.open('rb') as icon_file:
                    file_content = icon_file.read()
                    instance.icon.save(
                        filename,
                        ContentFile(file_content),
                        save=False
                    )
                
                print(f"  ✅ Иконка применена: {filename}")
                
            except IconTemplate.DoesNotExist:
                print(f"  ❌ Шаблон ID {template_id} не найден")
            except Exception as e:
                print(f"  ❌ ОШИБКА: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  ⚠️ Шаблон не выбран")
        
        if commit:
            instance.save()
            print(f"  💾 Сохранено в БД")
            
            # ПРОВЕРКА
            if instance.icon:
                print(f"  ✅ ПРОВЕРКА: Иконка в БД → {instance.icon.url}")
            else:
                print(f"  ❌ ПРОВЕРКА: Иконка НЕ сохранилась!")
        
        return instance