from django import forms
from .models import Grievance, GrievanceReply


class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = ['category', 'subject', 'message']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of your issue...',
                'id': 'id_subject',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your issue in detail...',
                'id': 'id_message',
            }),
        }
        labels = {
            'category': 'Issue Category',
            'subject': 'Subject',
            'message': 'Description',
        }


class AdminReplyForm(forms.ModelForm):
    class Meta:
        model = GrievanceReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Type your reply here. This will be sent to the employee via email...',
                'id': 'id_reply_message',
            }),
        }
        labels = {
            'message': 'Reply Message',
        }
