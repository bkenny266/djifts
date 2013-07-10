#DATA MANAGER APP - admin.py
#Interacts with the various app data models that are loaded from each game
#Game data is added to the database by using the add_game() function.

from datetime import date

from bs4 import BeautifulSoup
from games.models import Game
from .utility import create_game, import_player_data, get_soup, add_lines, get_front_page
from .date_util import process_date


#extends Game model and gives it functionality to create data

def add_game(game_num):
#INPUT: game_num is the unique id for the game, which is determined as follows
#		 		[season][season_subcategory][game_number] 
#				where season_subcategory 02 = regular season, 03 = playoffs
#				ex: 12020420
#					season = 12 (season starting in 2012)
#					season_subcategory = 02 (regular season)
#					game_number = 0420  (game is always four digits)
#THROWS EXCEPTION if there were any issues retrieving data from the game
#NO RETURN VALUE

#!!!STILL NEED TO IMPLEMENT DATABASE ROLLBACK IF UNSUCCESSFUL!!!

	try: 
		Game.objects.get(game_id=game_num)
		print "Game %s already exists in database." % game_num
		return False
	
	except Game.DoesNotExist:
		#if game doesn't exist in database, add it

		roster_soup = get_soup(game_num, 'roster')

		g = create_game(game_num, roster_soup)


		#import data separately for home and away team
		import_player_data(g.team_home, roster_soup)
		import_player_data(g.team_away, roster_soup)

		add_lines(g.team_home)
		add_lines(g.team_away)

		return True


def process_game_list():

	soup = get_front_page()

	games = soup.find_all("td", class_="active")

	for game in games:
		print process_date(game.text).year