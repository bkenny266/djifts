#DATA MANAGER APP - utility.py
#functions used by admin.py for creating data.

import requests
import re

from bs4 import BeautifulSoup
from nameparser import HumanName

from games.models import Game, TeamGame, PlayerGame, ShiftGame, TeamGameEvent, LineGame
from players.models import Player
from teams.models import Team

from .myfunks import convertToSecs, deleteAfter
from .eventprocessor import EventProcessor


class LineData(object):
#object used for storing game lines and accompanying data
	line_list = []
	start_time = None
	end_time = None
	shift_length = None

	def calculate_length(self):
	#calculates the length of time this shift has been on the ice
		length = self.end_time - self.start_time
		if self.start_time == None or self.end_time == None:
			raise(ValueError("start_time and end_time need to be set"))
		elif length < 0:
			raise (ValueError("start_time (%d) is greater than end_time (%d)" % (self.start_time, self.end_time)))
		else:
			self.shift_length = length



def get_front_page():
	r = requests.get('http://www.nhl.com/ice/gamestats.htm?fetchKey=20133ALLSATAll&sort=gameDate&viewName=teamRTSSreports')

	soup = BeautifulSoup(r.text)

	return soup

def get_soup(game_num, link_type):
	'''
	returns a beautiful soup object of different types of game data
	link_type is a string to specify data type - 'roster', 'shifts_home', 'shifts_away', or 'play_by_play'
	'''

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


def make_lines(teamgame):
	def process_shift_list(shift_item, list_index=0):
		#Makes sure shifts are in order of end times
		#If something is out of order, it will be pulled into a separate list
		#Each list will be in the correct order of end_time values

		try:
			#checks if the last item in list_index is >= to the value of shift_item
			#if not, recursively call this function and check again on the next level's list
			if shift_item.end_time >= shift_list[list_index][-1].end_time:
				shift_list[list_index].append(shift_item)

			else:
				process_shift_list(shift_item, list_index+1)

		except IndexError:
			#if an index error occurs, list does not exist at list_index
			shift_list.append([shift_item])
	

	def check_list(list_index, shift_index):
		#scans a list item and determines if the list should match this item
		#runs recursively to advance the list


		list_end = False

		#if shift index is the last in the list
		if shift_index >= len(shift_list[list_index]) - 1:
			list_end = True

		#if shift index was previously marked as the end of a list
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
			current_line_list.append(current)

			if not list_end:
				check_list(list_index, shift_index + 1)

		#set index to a special value if list is at the end
		if list_end:
			return_index = -1

		return return_index

	def __get_lowest__(line):

		lowest_end = 99999
		for shift in line:
			if shift.end_time < lowest_end:
				lowest_end = shift.end_time

		return lowest_end
	###############################################

	shift_list = []
	line_list = []
	
	#iterate through the shift list to order by end_times
	for item in teamgame.get_shifts():
		process_shift_list(item)

	
	shift_index = []

	#set index start position to zero for each list
	for x in range(0, len(shift_list)):
		shift_index.append(0)

	prev_end = 0
	game_end = shift_list[0][-1].end_time
		
	#Loop until end of the game is the lowest time from a line
	while(prev_end < game_end):
		current_line_list = []

		#runs checks on each list in the shift_array
		#each iteration of the loop returns the list index of where to begin next time
		for current_list_index in range(0, len(shift_list)):
			shift_index[current_list_index] = check_list(current_list_index, shift_index[current_list_index])
		
		#gets the value of the lowest end time on this shift, to use as next line's start time
		lowest_time = __get_lowest__(current_line_list)

		#instantiate LineData object and set values

		line_object = teamgame.get_line(current_line_list)

		shift_start = prev_end
		shift_end = lowest_time
		shift_length = shift_end - shift_start

		if shift_length < 0:
			raise(RuntimeError("Shift start time (%d) is later than end time (%d") % (shift_start, shift_end))

		if line_object:
			line_object.ice_time += shift_length
			line_object.num_shifts += 1
			line_object.save()
			print current_line_list
		else:
			line_model = LineGame.objects.create(teamgame = teamgame, 
				num_players = len(current_line_list),
				ice_time = shift_length,
				num_shifts = 1,
				goals = 0,
				hits = 0,
				blocks = 0,
				shots = 0)

			for shiftgame in current_line_list:
				line_model.playergames.add(shiftgame.playergame)

			

		#set a new value prev_end to be used in the next iteration
		prev_end = lowest_time

		line_list.append(current_line_list)

		#reset line_object for next loop
		line_object = None


	return line_list


def import_lines(teamgame):

	game_lines = make_lines(teamgame)



def import_events(game):
	event_soup = get_soup(game.pk, 'play_by_play')

	events = EventProcessor(event_soup)

	#get objects and initials for home and away teams
	home_team_initials = game.team_home.team.initials
	away_team_initials = game.team_away.team.initials

	for event in events.flatten():
		if event.event_team_initials == home_team_initials:
			player = PlayerGame.objects.get(team = game.team_home, player__number = event.event_player)
		elif event.event_team_initials == away_team_initials:
			player = PlayerGame.objects.get(team = game.team_away, player__number = event.event_player)
		else:
			raise(ValueError("Event team initials (%s) do not match data" % event.event_team_initials))
	
		TeamGameEvent.objects.create(playergame=player, event_time=event.event_time_in_seconds, event_type=event.event_type)
	