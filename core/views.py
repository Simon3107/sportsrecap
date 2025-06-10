from django.shortcuts import render, get_object_or_404, redirect
from .models import Sport, Match, Comment
from collections import defaultdict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import CommentForm
# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def home(request):
    sports = Sport.objects.all()
    data = []

    for sport in sports:
        matches = Match.objects.filter(sport=sport).order_by('-match_date')
        tournaments = defaultdict(list)
        for match in matches:
            tournaments[match.tournament].append(match)
        data.append({
            'sport': sport,
            'tournaments': dict(tournaments)
        })

    return render(request, 'index.html', {'data': data})

def sport_list(request):
    return render(request, 'sport_list.html')

def match_detail(request, id):
    match = get_object_or_404(Match, pk=id)
    comments = Comment.objects.filter(match=match).order_by('-created_at')
    return render(request, 'match_detail.html', {
        'match': match,
        'comments': comments,
        'comment_form': CommentForm()
    })

@login_required
def add_comment(request, match_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.match = get_object_or_404(Match, pk=match_id)
            comment.save()
            return JsonResponse({
                'success': True,
                'comment': comment.text,
                'user': comment.user.username,
                'date': comment.created_at.strftime("%d.%m.%Y %H:%M")
            })
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def profile(request):
    return render(request, 'profile.html')


def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    matches = Match.objects.filter(sport=sport)
    return render(request, 'sport_matches.html', {
        'sport': sport,
        'matches': matches
    })


class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Erfolgreich eingeloggt!")  # Erfolgsmeldung
        return response

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Erfolgreich ausgeloggt!")
        return super().dispatch(request, *args, **kwargs)