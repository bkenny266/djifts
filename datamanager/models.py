from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import datetime
import requests
import re
from bs4 import BeautifulSoup
from teams.models import Team
import datamanager.admin


games_url =u"http://www.nhl.com/ice/gamestats.htm?pg=2"

class GameList(models.Model):
	'''
	Holds game header info from a season with indicator of 
	if it's been processed.  Includes load and reload methods for  
	processing game line data'''

	game_id = models.IntegerField(primary_key = True)
	date = models.DateField()
	processed = models.BooleanField(default = False)
	home_team = models.ForeignKey(Team, related_name = "home")
	away_team = models.ForeignKey(Team, related_name = "away")


	orig_season_id = models.CharField(max_length = 8)
	orig_game_key = models.CharField(max_length = 6)


	def revert_game_id(self):
		'''Reverts a game_id back to original form to download data from web'''

		season = self.game_id / 1000000
		season = "20" + str(season) + "20" + str(season+1)

		game = "0" + str(self.game_id % 1000000)

		return (season, game)

	def get_orig_game_id(self):
		'''
		returns a tuple of orig_season_id and orig_game_key to be used
		in data downloads
		'''
		return (self.orig_season_id, self.orig_game_key)


	def load_game_data(self):
		self.processed = datamanger.admin.add_game(self.get_orig_game_id())


	@classmethod
	def load_game_info(cls, game_tuple):
		'''Receives a tuple of (game_id, date, home_team, away_team) and 
		uses it to load data to the GameList model'''
		game_id, date, home_team, away_team = game_tuple
		try:
			GameList.objects.get(pk=game_id)
			return False
		except ObjectDoesNotExist:
			g = GameList(pk=game_id, date=date, home_team=home_team,
				away_team=away_team)
			g.orig_season_id, g.orig_game_key = g.revert_game_id()
			g.save()
			return True

	@classmethod
	def parse_game_info(cls, gamedata):
		'''Receives a BeautifulSoup formatted list of game's HTML tags
		Returns the game's id, date, and Team objects for each team'''

		#SETTINGS FOR SCRAPING
		URL_INDEX = 0
		HOME_TEAM_INDEX = 1
		AWAY_TEAM_INDEX = 3
		url = gamedata[URL_INDEX].a['href']
		date = gamedata[URL_INDEX].text
		#grabs last part of URL, strips out "GS" and extension
		URL_PARSE_REGEX = r'^.*/(.*)/GS(.*)\.'

		parsed_url = re.match(URL_PARSE_REGEX, url)
		season = parsed_url.group(1)
		game_id = parsed_url.group(2)
		if game_id == None or season == None:
			raise(Exception("Game ID parse failed"))

		game_id = cls.convert_game_id(season, game_id)
		date = cls.convert_date(date)
		home_team_city_name = gamedata[HOME_TEAM_INDEX].text
		away_team_city_name = gamedata[AWAY_TEAM_INDEX].text

		home_team = Team.objects.get(city_name = home_team_city_name)
		away_team = Team.objects.get(city_name = away_team_city_name)

		return (game_id, date, home_team, away_team)

	@classmethod
	def convert_date(cls, date_in):
		'''Receives a date in string format, returns a datetime.date object'''
		#date's format ex: Mar 12, '14
		FORMAT = "%b %d '%y"
		try:
			dt = datetime.datetime.strptime(date_in, FORMAT)
		except:
			raise(ValueError("%s not in expected format - %s" % (date_in, FORMAT)))
		
		return dt.date()

	@classmethod
	def convert_game_id(cls, season, game_id):
		'''Receives scraped season and game_id strings, 
			returns an id value reformatted as such:
		 		[season][season_subcategory][game_number] 
				where season_subcategory is 02 = regular season, 03 = playoffs
				ex in: ("2012", "020420")	ex: out: 12020420
					season = 12 (season starting in 2012)
					season_subcategory = 02 (regular season)
					game_number = 0420  (game is always four digits)		
		'''
		season = season[2:4]
		formatted_id = season + game_id

		#checks if game_id starts with valid identifier
		check_game_id = game_id[0:2]
		if check_game_id != "02" and check_game_id !="03":
			raise(Exception("game_id starts with %s - should start" \
				" with 02 or 03" % check_game_id))

		if len(formatted_id) != 8:
			raise(Exception("game_id is length %s - should be length 8" %
				len(formatted_id)))
		
		formatted_id = int(formatted_id)
		#check that first two digits are valid
		check_value = formatted_id / 1000000
		if check_value < 12 or check_value > 19:
			raise(Exception("season value is %d - should be between 12 and 19" %
				check_value))

		return formatted_id


def get_test_data():
	r = requests.get("http://www.nhl.com/ice/gamestats.htm?pg=2")
	soup = BeautifulSoup(r.text.encode("utf-8"))
	items = soup.find_all("td", class_="active")

	return list(items[0].parent.children)

