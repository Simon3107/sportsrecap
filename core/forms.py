from django import forms
from .models import Comment, Match, Tournament

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Schreib einen Kommentar...'})
        }

