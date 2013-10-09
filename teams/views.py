# Create your views here.

from django.shortcuts import render
from django.db import models

from teams.models import Team
from games.models import Game

def team_list(request):

	t = Team.objects.all()

	return render(request, 'team_select.html', {'teams' : t})

def get_team_page(request, team_id):

	team = Team.objects.get(pk=int(team_id))
	g = Game.objects.filter(models.Q(team_away__team=team_id) | models.Q(team_home__team=team_id))


	return render(request, 'team_view.html', {'games' : g, 'team_id' : int(team_id), 'team' : team})

