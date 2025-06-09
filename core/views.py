from django.shortcuts import render, get_object_or_404, redirect
from .models import Sport, Match
from collections import defaultdict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
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
    return render(request, 'match_detail.html', {'match': match})

def profile(request):
    return render(request, 'profile.html')


def sport_matches(request, id):
    sport = get_object_or_404(Sport, pk=id)
    matches = Match.objects.filter(sport=sport)
    return render(request, 'sport_matches.html', {
        'sport': sport,
        'matches': matches
    })

def logout_view(request):
    logout(request)
    return redirect('index')
