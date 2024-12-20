from .models import Comment
from mdeditor.widgets import MDEditorWidget
from django import forms
import logging

logger = logging.getLogger(__name__)

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=30)
    your_email = forms.EmailField()
    to_whom = forms.EmailField()
    comments = forms.CharField(required=False, widget=MDEditorWidget())

    def clean(self):
        """
        Обрабатывает валидацию формы и логирует ошибки.
        """
        cleaned_data = super().clean()
        try:
            # Дополнительная валидация, если необходимо
            if not cleaned_data.get('name'):
                raise forms.ValidationError("Имя не может быть пустым")
            if not cleaned_data.get('your_email'):
                raise forms.ValidationError("Ваш email не может быть пустым")
            if not cleaned_data.get('to_whom'):
                raise forms.ValidationError("Email получателя не может быть пустым")
        except forms.ValidationError as e:
            logger.error(f"Ошибка валидации формы: {e}")
            raise
        return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']
        widgets = {
            'body': MDEditorWidget(),
        }

    def clean(self):
        """
        Обрабатывает валидацию формы и логирует ошибки.
        """
        cleaned_data = super().clean()
        try:
            # Дополнительная валидация, если необходимо
            if not cleaned_data.get('name'):
                raise forms.ValidationError("Имя не может быть пустым")
            if not cleaned_data.get('email'):
                raise forms.ValidationError("Email не может быть пустым")
            if not cleaned_data.get('body'):
                raise forms.ValidationError("Комментарий не может быть пустым")
        except forms.ValidationError as e:
            logger.error(f"Ошибка валидации формы: {e}")
            raise
        return cleaned_data


class SearchForm(forms.Form):
    query = forms.CharField()

    def clean_query(self):
        """
        Обрабатывает валидацию поля поиска и логирует ошибки.
        """
        query = self.cleaned_data.get('query')
        try:
            if not query:
                raise forms.ValidationError("Запрос не может быть пустым")
        except forms.ValidationError as e:
            logger.error(f"Ошибка валидации поля поиска: {e}")
            raise
        return query
