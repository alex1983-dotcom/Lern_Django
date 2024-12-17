from django import forms
from .models import Comment
from mdeditor.widgets import MDEditorWidget

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
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

class SearchForm(forms.Form):
    query = forms.CharField()
