from django import forms

class QuestionForm(forms.Form):
    question = forms.CharField(
        label='Your Question',
        min_length=10,
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'e.g. What is the difference between a t-test and a z-test?',
            'class': 'form-control',
        })
    )