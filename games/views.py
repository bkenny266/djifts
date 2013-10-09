# Create your views here.

from django.views.generic import ListView, DetailView, View
from django.db import models
from games.models import Game
from teams.models import Team
from django.http import HttpResponse
from django.shortcuts import render

class GameListView(ListView):
	model = Game
	template_name = "game_list.html"


class GameDetailView(DetailView):
	model = Game
	template_name = "game_detail.html"

	
	def get_context_data(self, **kwargs):

				
		context = super(GameDetailView, self).get_context_data(**kwargs)


		thisgame = Game.objects.get(pk=self.kwargs['pk'])

		context['home'] = thisgame.roster_home()
		context['away'] = thisgame.roster_away()

		return context
		

class TestView(DetailView):
	pass
	#model = games


	#def get_context_data(self, **kwargs):
	#	context = super(TestView, self).get_context_data(**kwargs)
		#context['home_list'] = 


def team_list(request):

	t = Team.objects.all()

	return render(request, 'team_select.html', {'teams' : t})

def get_team_page(request, team_id):

	team = Team.objects.get(pk=int(team_id))
	g = Game.objects.filter(models.Q(team_away__team=team_id) | models.Q(team_home__team=team_id))


	return render(request, 'team_view.html', {'games' : g, 'team_id' : int(team_id), 'team' : team})



