'''
DATAMANAGER - event_track.py
'''

import re

class EventProcessor():

	goals = []
	shots = []
	blocks = []
	hits = []

	event_types = ['GOAL', 'SHOT', 'HIT', 'BLOCK']

	def __init__(self, soup):

		for event in self.event_types:
			type_objects = soup.find_all('td', text=event)

			for current_object in type_objects:
				#period is 6 siblings back
				period = current_object.previous_sibling.previous_sibling.previous_sibling.previous_sibling.previous_sibling.previous_sibling.text
				time = current_object.previous_sibling.previous_sibling.next_element
				data_block = current_object.next_sibling.next_sibling.text

				parsed = re.match(r'^\b*([A-Z.]+)\D+#(\d{1,2})', data_block)
				team_initials = parsed.group(1)
				player_number = parsed.group(2)

				e = Event(event, team_initials, player_number, period, time)

				if event == 'GOAL':
					self.goals.append(e)
				elif event == 'SHOT':
					self.shots.append(e)
				elif event == 'HIT':
					self.hits.append(e)
				elif event == 'BLOCK':
					self.blocks.append(e)
				else:
					raise(ValueError, "Invalid event - %s" % event)



class Event(object):
	event_team_initials = ''
	event_type = ''
	event_player_number = ''
	event_period = ''
	event_time = ''
	event_time_in_seconds = ''

	def __init__(self, event_type, event_team_initials, event_player, event_period, event_time):
		self.event_type = event_type
		self.event_player = int(event_player)
		self.event_period = int(event_period)
		self.event_time = event_time

		if event_team_initials == "L.A":
			self.event_team_initials = "LAK"
		
		elif event_team_initials == "S.J":
			self.event_team_initials = "SJS"

		elif event_team_initials == "T.B":
			self.event_team_initials ="TBL"

		elif event_team_initials == "N.J":
			self.event_team_initials = "NJD"

		else:
			self.event_team_initials = event_team_initials

		self.event_team_initials = event_team_initials

		self.__convert_to_seconds__()

	def __convert_to_seconds__(self):
		parsed = re.match('^(\d{1,2}):(\d{2})$', self.event_time)
		timeMins = int(parsed.group(1))
		timeSecs = int(parsed.group(2))
		self.event_time_in_seconds = timeMins * 60 + timeSecs + ((self.event_period * 20 - 20) * 60)

