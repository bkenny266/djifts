from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import datetime
import requests
import re
from bs4 import BeautifulSoup
from teams.models import Team


# Create your models here.
class GameList(models.Model):
	'''Holds games ids from a season with information showing if it's been processed
	Includes load and reload methods to process game line data'''

	game_key = models.IntegerField(primary_key = True)
	date = models.DateField()
	processed = models.BooleanField(default = False)
	home_team = models.ForeignKey(Team, related_name = "home")
	away_team = models.ForeignKey(Team, related_name = "away")


def load_game_to_list(game_tuple):
	'''Receives a tuple of (game_id, date, home_team, away_team) and 
	uses it to load data to the GameList model'''
	game_id, date, home_team, away_team = game_tuple
	try:
		GameList.objects.get(pk=game_id)
		return False
	except ObjectDoesNotExist:
		GameList.objects.create(pk=game_id, date=date, home_team=home_team, away_team=away_team)
		return True

def parse_game_info(gamedata):
	'''Receives a BeautifulSoup formatted list of game's HTML tags
	Returns the game's id, date, and Team objects for each team'''

	#SETTINGS FOR SCRAPING
	LINK_INDEX = 0
	HOME_TEAM_INDEX = 1
	AWAY_TEAM_INDEX = 3
	link = gamedata[LINK_INDEX].a['href']
	date = gamedata[LINK_INDEX].text
	#grabs last part of URL, strips out "GS" and extension
	LINK_PARSE_REGEX = r'^.*/GS(.*)\.'

	game_id = re.match(LINK_PARSE_REGEX, link).group(1)
	if game_id == None:
		raise(Exception("Game ID parse failed"))

	date = convert_date(date)
	home_team_city_name = gamedata[HOME_TEAM_INDEX].text
	away_team_city_name = gamedata[AWAY_TEAM_INDEX].text

	home_team = Team.objects.get(city_name = home_team_city_name)
	away_team = Team.objects.get(city_name = away_team_city_name)

	return (game_id, date, home_team, away_team)

def convert_date(date_in):
	"""Receives a date in string format, returns a datetime.date object"""
	#date's format ex: Mar 12, '14
	FORMAT = "%b %d '%y"
	dt = datetime.datetime.strptime(date_in, FORMAT)
	return dt.date()

def get_test_data():
	r = requests.get("http://www.nhl.com/ice/gamestats.htm")
	soup = BeautifulSoup(r.text.encode("utf-8"))
	items = soup.find_all("td", class_="active")

	return list(items[0].parent.children)
