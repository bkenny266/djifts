#DATA MANAGER APP - utility.py
#functions used by admin.py for creating data.

import requests
import re

from bs4 import BeautifulSoup
from nameparser import HumanName

'''
DATAMANAGER - utility.py
'''

from games.models import Game, TeamGame, PlayerGame, ShiftGame
from players.models import Player
from teams.models import Team
from .myfunks import convertToSecs, deleteAfter

def get_front_page():
	r = requests.get('http://www.nhl.com/ice/gamestats.htm?fetchKey=20133ALLSATAll&sort=gameDate&viewName=teamRTSSreports')

	soup = BeautifulSoup(r.text)

	return soup

def get_soup(game_num, link_type):
	#returns beautiful soup object

	#extract season number from game_id and use it for the data source URL
	season_num = game_num / 1000000
	season_string = "20%d20%d" % (season_num, season_num + 1)

	#extract game_string from game_id and use it for the data source URL
	game_string = "%d" % game_num
	game_string = game_string[2:]

	if link_type == 'roster':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/RO' + game_string + '.HTM')

	elif link_type == 'shifts_home':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/TH' + game_string + '.HTM')

	elif link_type == 'shifts_away':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/TV' + game_string + '.HTM')

	elif link_type == 'play_by_play':
		r = requests.get('http://www.nhl.com/scores/htmlreports/' + season_string + '/PL' + game_string + '.HTM')

	else:
		raise(ValueError("Valid link_type arguments are 'roster', 'play_by_play', 'shifts_home', and 'shifts_away'"))


	soup = BeautifulSoup(r.text)

	if soup.title.text == "404 Not Found":
		raise(ValueError("Data could not be found at this address for game %s in season %s" % (game_string, season_string)))

	return soup


def create_game(game_num, roster_soup):

	#pull team name data from txt - first two instances of class teamHeading
	teams = roster_soup.find_all('td', class_ = "teamHeading")
	away_name = teams[0].text.encode('ASCII')
	home_name = teams[1].text.encode('ASCII')

	#Creates TeamGame objects home, away
	away = TeamGame.objects.create(team = Team.objects.get(name=away_name))
	home = TeamGame.objects.create(team = Team.objects.get(name=home_name))

	game = Game(game_id=game_num, team_home=home, team_away=away)
	game.save()

	return game



def import_player_data(team, roster_soup):

	#Determines if the team is the home or away team for the game
	if team.is_home():
		homeaway = "home"
		game_id = team.home.all()[0].game_id
	elif team.is_away():
		homeaway = "away"
		game_id = team.away.all()[0].game_id
	else:
		raise(Exception("TeamGame object (%s) has no home or away status") % team)

	##GET ROSTER
	

	#Indicates the list index of "roster" from which to begin iterating
	START_ROSTER = 3

	#Indices of player data within each player's 'roster' tags
	POSITION_INDEX = 3
	NAME_INDEX = 5
	NUMBER_INDEX = 1

	#number is a value to determine which index of the BeautifulSoup object to extract data from
	if homeaway == "home":
		number = 1
	else:
		number = 0

	#Sets 'roster' to a BeautifulSoup object which contains the data for a team's roster
	roster = roster_soup.find_all("td", text="#")[number].parent.parent

	#Iterates over the 'roster', skipping every other item (null tags)
	for i in range(START_ROSTER, len(roster), 2):

		position = roster.contents[i].contents[POSITION_INDEX].text.encode('ASCII')

		name = roster.contents[i].contents[NAME_INDEX].text.encode('ASCII')
		hname = HumanName(name)
		first_name = hname.first
		last_name = hname.last

		number = roster.contents[i].contents[NUMBER_INDEX].text.encode('ASCII')

		#Checks if player exists or if multiple players with this name.  
		#If player does not exist, add to Player database and PlayerGame database.
		#If player exists, add to PlayerGame database.
		try:
			p = Player.objects.get(first_name=first_name, last_name=last_name)
			PlayerGame.objects.create(player=p, team=team)
		except Player.MultipleObjectsReturned:
			#Check if multiple players in the league or if player has been traded
			print "Multiple players with this name"
			pass
		except Player.DoesNotExist:
			#Check if new player or data error
			p = Player.objects.create(first_name=first_name, last_name=last_name, position=position, number=number)
			PlayerGame.objects.create(player=p, team=team)
			print "Added - " + p.first_name + " " + p.last_name + " (" + p.position + ") " + team.team.initials 
	
	
	###GET SHIFTS

	if homeaway == "home":
		shift_soup = get_soup(game_id, 'shifts_home')
	else:
		shift_soup = get_soup(game_id, 'shifts_away')

	#Get list of players from BeautifulSoup object
	players = shift_soup.find_all('td', class_='playerHeading')
	
	for player in players:
		playerName = HumanName(player.text)

		#Strip out player's number from name
		playerName.last = re.sub("\d+", "", playerName.last).strip()
		playerObj = Player.objects.get(first_name=playerName.first, last_name=playerName.last)

		#Create new object for PlayerGame and save to database
		playerGameObj = PlayerGame.objects.get(player=playerObj, team=team)

		#Parse the individual player BeautifulSoup object for shift data
		shift = player.parent.next_sibling.next_sibling.next_sibling.next_sibling
		shift_list = shift.find_all("td")

		#If 6 items in shift_list object, it matches the structure of valid shift data
		while(len(shift_list) == 6):
			period = int(shift_list[1].text)
			timeOn = deleteAfter(shift_list[2].text, '/')
			timeOn = convertToSecs(timeOn, period)
			timeOff = deleteAfter(shift_list[3].text, '/')
			timeOff = convertToSecs(timeOff, period)


			ShiftGame.objects.create(playergame=playerGameObj, start_time=timeOn, end_time=timeOff)

			#Get next shift for this player
			shift = shift.next_sibling.next_sibling
			shift_list = shift.find_all("td")

def add_lines(teamgame):

	shift_list = []
	line_list = []

	def process_shift_list(shift_item, list_index):
		#Function to make sure shift end_time values are in order
		#If something is out of order, will pull it into a separate list
		#Each list will be in the correct order of end_time values

		try:
			#checks if the last item in list_index is equal to or greater than 
			#the value of shift_item.
			#if not, recursively call this function and check again on the next level's list
			if shift_item.end_time >= shift_list[list_index][-1].end_time:
				shift_list[list_index].append(shift_item)

			else:
				process_shift_list(shift_item, list_index+1)

		except IndexError:
			#if an index error occurs, list does not exist at list_index
			#creates a new list and appends the value to it
			shift_list.append([shift_item])


	def make_lines():

		def check_list(list_index, shift_index):
			#determines how to handle the list data for each shift
			#recursive function, runs on itself to advance the list


			list_end = False

			#if shift index is the last in the list
			if shift_index >= len(shift_list[list_index]) - 1:
				list_end = True

			#if shift index was previously marked as the last of a list
			if shift_index == -1:
				#mark as end of list, point to end of list
				list_end = True
				shift_index = len(shift_list[list_index]) - 1

			#initializes return value to current value
			return_index = shift_index

			#set a variable to current list object
			current = shift_list[list_index][shift_index]

			#no further actions if current item has not yet been reached
			if current.start_time > prev_end:
				pass

			#if current item is no longer relevant, move ahead in list and re-check
			#note: advances return index
			elif current.end_time <= prev_end:
				if not list_end:
					return_index = check_list(list_index, shift_index + 1)

			#if current item is part of the active shift, add to list and check the next item
			#note: does not advance the return index
			elif current.start_time <= prev_end and prev_end < current.end_time:
				current_line.append(current)

				if not list_end:
					check_list(list_index, shift_index + 1)

			#set index to a special value if list is at the end
			if list_end:
				return_index = -1

			return return_index
		###############################################


		#set index start position to zero for each list
		shift_index = []
		
		for x in range(0, len(shift_list)):
			shift_index.append(0)

		prev_end = 0
		game_end = shift_list[0][-1].end_time
			
		#Loop until end of the game is the lowest time from a line
		while(prev_end < game_end):
			current_line = []

			#runs checks on each list in the shift_array
			#each iteration of the loop returns the list index of where to begin next time
			for current_list_index in range(0, len(shift_list)):
				shift_index[current_list_index] = check_list(current_list_index, shift_index[current_list_index])
				
			#get the lowest end_time and use it to calculate the next shift
			prev_end = get_lowest(current_line)
			line_list.append(current_line)

	def make_lines():

			def check_list(list_index, shift_index):
				#determines how to handle the list data for each shift
				#recursive function, runs on itself to advance the list


				list_end = False

				#if shift index is the last in the list
				if shift_index >= len(shift_list[list_index]) - 1:
					list_end = True

				#if shift index was previously marked as the last of a list
				if shift_index == -1:
					#mark as end of list, point to end of list
					list_end = True
					shift_index = len(shift_list[list_index]) - 1

				#initializes return value to current value
				return_index = shift_index

				#set a variable to current list object
				current = shift_list[list_index][shift_index]

				#no further actions if current item has not yet been reached
				if current.start_time > prev_end:
					pass

				#if current item is no longer relevant, move ahead in list and re-check
				#note: advances return index
				elif current.end_time <= prev_end:
					if not list_end:
						return_index = check_list(list_index, shift_index + 1)

				#if current item is part of the active shift, add to list and check the next item
				#note: does not advance the return index
				elif current.start_time <= prev_end and prev_end < current.end_time:
					current_line.append(current)

					if not list_end:
						check_list(list_index, shift_index + 1)

				#set index to a special value if list is at the end
				if list_end:
					return_index = -1

				return return_index
			###############################################


			#set index start position to zero for each list
			shift_index = []
			
			for x in range(0, len(shift_list)):
				shift_index.append(0)

			prev_end = 0
			game_end = shift_list[0][-1].end_time
				
			#Loop until end of the game is the lowest time from a line
			while(prev_end < game_end):
				current_line = []

				#runs checks on each list in the shift_array
				#each iteration of the loop returns the list index of where to begin next time
				for current_list_index in range(0, len(shift_list)):
					shift_index[current_list_index] = check_list(current_list_index, shift_index[current_list_index])
					
				#get the lowest end_time and use it to calculate the next shift
				prev_end = get_lowest(current_line)
				line_list.append(current_line)

	def get_lowest(line):

		lowest_end = 99999
		for shift in line:
			if shift.end_time < lowest_end:
				lowest_end = shift.end_time

		return lowest_end


	for shift in teamgame.get_shifts():
		process_shift_list(shift, 0)

	make_lines()

	return line_list





