djifts
------

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
Requires Python 2.7, Django 1.5.1, and the following python modules: 
BeautifulSoup, requests, nameparser


The Applications
----------------

Datamanager: 
	Includes methods used for downloading, processing, and storing data.

	-admin.py - currently acts as the "front end" for downloading game data. 
	The user can run the add_game() method to download data for a particular 
	game.  
	
	-utility.py - contains methods used by admin.py to retrieve game roster, 
	player shift times, generate the line combinations from each NHL game, 
	and store all of this in the database.
	
	-eventprocessor.py - special utility module that implements a class for 
	downloading	and storing data for the different 'event types' that occur 
	during a game (shots, hits,	blocks, goals)
	

Games:  Includes models and views for interacting with data on a "game" level.

Teams:  Includes models and views for interacting with data on a "team" level.
	
Players:  Includes models and views for interacting with data on a "player" level.
	

Next Steps
----------
-Refactor the datamanager app for tighter encapsulation; should make things easier to test
-Implement rigorous testing on line matching logic.  
-Need to be particularly vigilent about confirming data being downloaded
to the database is correct and implement a rollback system in the event of failure.  
-Improve templates and site usability.  Need to learn more about Bootstrap and figure out
how to design an appealing front-end for the website.
-Try to improve PEP8 compliance
-Need to implement testing structure across the board.  Unit tests, integration tests, etc.
-Implement a system to continuously scan the NHL games page and  download data
for new games as they occur.



