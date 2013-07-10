# Create your views here.

from django.views.generic import ListView, DetailView, View
from games.models import Game
from django.http import HttpResponse

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
		