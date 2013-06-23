# Create your views here.
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.shortcuts import render

from gamedata.models import Player

def show_games(request):

	pname = Player.objects.get(pk=1)

	c = Context( {'player_name': pname})
	
	return render(request, 'templates.html', c)
