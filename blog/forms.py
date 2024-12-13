from django import forms


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    your_email = forms.EmailField()
    to_whom = forms.EmailField()
    comments = forms.CharField(required=False,
                               widget=forms.Textarea)
