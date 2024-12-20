from django import forms
from .models import Comment
from mdeditor.widgets import MDEditorWidget

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=30)
    your_email = forms.EmailField()
    to_whom = forms.EmailField()
    comments = forms.CharField(required=False, widget=MDEditorWidget())

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']
        widgets = {
            'body': MDEditorWidget(),
        }

from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(
        label='Search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите текст для поиска...',
            'class': 'form-control'  # Класс для стилизации
        })
    )