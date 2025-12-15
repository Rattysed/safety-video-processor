from django import forms
from .common import *
import json

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class FileFieldForm(forms.Form):
    file_field = MultipleFileField(widget=forms.HiddenInput())
    points = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        files = self.files.getlist('file_field')
        for file in files:
            if not validate_file_extensions(ALLOWED_FILE_EXTENSIONS, file.name):
                raise forms.ValidationError(f"{file.name} не является .jpg или .png файлом.")
        return super().clean()
    
    def clean_points(self):
        points_str = self.cleaned_data['points']
        try:
            points = json.loads(points_str)
            # Валидация структуры
            for point in points:
                if len(point) != 2:
                    raise forms.ValidationError("Каждая точка должна содержать 2 координаты")
                if not all(isinstance(coord, int) for coord in point):
                    raise forms.ValidationError("Координаты должны быть целыми числами")
            return points
        except Exception as e:
            print(e)
            raise