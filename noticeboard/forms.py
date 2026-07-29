# forms.py

from django import forms
from .models import NoticeBoard


class NoticeBoardForm(forms.ModelForm):

    class Meta:

        model = NoticeBoard

        fields = [
            'title',
            'notice_type',
            'message_type',
            'message',
            'is_active'
        ]

        widgets = {

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notice title'
            }),

            'notice_type': forms.Select(attrs={
                'class': 'form-select'
            }),

            'message_type': forms.Select(attrs={
                'class': 'form-select'
            }),

            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter notice message'
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }