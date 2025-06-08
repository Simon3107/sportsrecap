from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Sport(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)

    def __str__(self):
        return self.name
 

class Match(models.Model):

    TOURNAMENT_CHOICES = [
        ('NATIONS_LEAGUE', 'Nations League'),
        ('CHAMPIONS_LEAGUE', 'Champions League'),
        ('BUNDESLIGA', 'Bundesliga'),
        ('PREMIER_LEAGUE', 'Premier League'),
        ('NHL', 'NHL'), 
        ('DEL', 'Deutsche Eishockey Liga'),
        ('NBA', 'NBA'),  # USA
        ('BBL', 'Basketball Bundesliga'),  # Deutschland
        ('EUROLEAGUE', 'EuroLeague'),  # Europa
        ('WIMBLEDON', 'Wimbledon'),
        ('ROLAND_GARROS', 'Roland Garros (French Open)'),
    ]

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    score = models.CharField(max_length=20)
    yt_url = models.URLField(blank=True, null=True)
    match_date = models.DateField()
    tournament = models.CharField(max_length=50, choices=TOURNAMENT_CHOICES)
    def __str__(self):
        return f"{self.team1} vs {self.team2} – {self.match_date}"

class Comment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.created_at.strftime('%Y-%m-%d')}"
