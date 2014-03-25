# Create your views here.
import json
from django.http import HttpResponse

from games.models import Game
from datamanager.models import GameProcessor




def game_request(request, game_id):

	game = Game.objects.get(pk=game_id)
	json_data = game.get_json()


	return HttpResponse(json.dumps(json_data, indent=4), content_type="application/json")


def game_list_request(request, *arg):
	if arg:
		json_data = GameProcessor.get_json(team_initials=arg[0],)
	else:
		json_data = GameProcessor.get_json()

	return HttpResponse(json.dumps(json_data, indent=4), content_type="application/json")