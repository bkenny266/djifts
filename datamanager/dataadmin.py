'''
DATA MANAGER APP - admin.py
Interacts with the various app data models that are loaded from each game
Game data is added to the database by using the add_game() function.
'''

from datetime import date
import ipdb

from bs4 import BeautifulSoup
from games.models import Game, LineGame
from .utility import create_game, import_player_data, get_soup, make_lines, import_events, process_penalties, check_penalty_lines
from .date_util import process_date
from .eventprocessor import EventProcessor

def add_game(game_num):
	'''
	Master function for loading game data
	in: game_id key
	out: data loaded to model, returns a bool indicating success
	'''

	#!!!STILL NEED TO IMPLEMENT DATABASE ROLLBACK IF UNSUCCESSFUL!!!

	try: 
		#if already exists, nothing to do here
		Game.objects.get(game_id=game_num)
		print "Game %s already exists in database." % game_num
		return False
	except Game.DoesNotExist:
		#if game doesn't exist in database, add it
		roster_soup = get_soup(game_num, 'roster')

		g = create_game(game_num, roster_soup)

		#import data separately for home and away team

		event_soup = get_soup(game_num, 'play_by_play')
		events = EventProcessor(event_soup)
		
		import_player_data(g.team_home, roster_soup)
		import_player_data(g.team_away, roster_soup)

		process_penalties(g, events.penalties)
		#ipdb.set_trace()

		make_lines(g.team_home)
		make_lines(g.team_away)

		#now that lines are processed, calculate ice_time_str for all LineGames
		teams = [g.team_home, g.team_away]
		for team in teams:
			for lg in LineGame.objects.filter(teamgame=team):
				lg.set_ice_time_str()

		check_penalty_lines(g)

		import_events(g, events)

		return True



###GAME_LIST STILL TO COME
##Scans the list of games, adds an 
def process_game_list():

	soup = get_front_page()

	games = soup.find_all("td", class_="active")

	for game in games:
		print process_date(game.text).year