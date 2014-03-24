#djifts

Overview: This is a Django/Python web application currently in development. 
The goal of this project is to collect data from NHL games related to
player line combinations and aggregate statistics to measure the performance
of these line combinations.  The stats that we will measure are goals, shots,
hits, shot blocks, and ice time.  By collecting data from each hockey game over
the course of a season, we can determine the lines that are the top performers 
in each of these statistical categories.  The plan is to allow users to view 
lists of top performing lines over various lengths of time and on various 
scopes: league-wide, team-wide, and game-wide.


To install
----------
	```
	pip install -r requirements.txt
	```


Requires Python 2.7, Django 1.5.1, and the following python modules: 
BeautifulSoup, requests, nameparser


#The Applications

###API: 
Export json game data - currently linked to data at the Game level via the
following url pattern:

	```
	/api/game/[game_id]
	```

###Datamanager: 
Includes methods used for downloading, processing, and storing data.

*models.py - stores game headers and methods to load game data.
*utility.py - primary methods for loading game data includes importing  
shift times, calculating line combinations, and writing to database.
*eventprocessor.py - special utility module that implements a class for 
importing data regarding the different 'event types' occurring 
during the game (shots, hits, blocks, goals)
	
###Games: 
Includes models and views for interacting with data on a "game" level.

###Teams:  
Includes models and views for interacting with data on a "team" level.
	
###Players:  
Includes models and views for interacting with data on a "player" level.
	

#Next Steps
*API for json data service 
*Refactor the datamanager app for tighter encapsulation; should make things easier to test
*Implement rigorous testing on line matching logic.  
*Need to be particularly vigilent about confirming data being downloaded
to the database is correct and implement a rollback system in the event of failure.  
*Improve templates and site usability.  Need to learn more about Bootstrap and figure out
how to design an appealing front-end for the website.
*Try to improve PEP8 compliance
*Need to implement testing structure across the board.  Unit tests, integration tests, etc.
*Implement a system to continuously scan the NHL games page and  download data
for new games as they occur.


#Other things to do
*New GameManager type with a "create" function that inializes a 
list containing both home team and away team
