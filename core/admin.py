from django.contrib import admin
# Register your models here.
from .models import Sport, Match, Comment, Team


admin.site.register(Sport)
admin.site.register(Match)
admin.site.register(Comment)
admin.site.register(Team)
