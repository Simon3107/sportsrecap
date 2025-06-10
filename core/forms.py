from django import forms
from .models import Comment, Match, Tournament

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Schreib einen Kommentar...'})
        }

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamische Filterung der Turniere
        if 'sport' in self.data:
            try:
                sport_id = int(self.data.get('sport'))
                self.fields['tournament'].queryset = Tournament.objects.filter(sport_id=sport_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['tournament'].queryset = self.instance.sport.tournament_set