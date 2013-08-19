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

Djifts: Standard Django stuff to include settings, urls, etc


Datamanager: Includes methods used for downloading, processing, and storing data. 

	-admin.py - currently acts as the "front end" for downloading game data.  The
	user can run the add_game() method to download data for a particular game.  
	
	-utility.py - contains methods used by admin.py to retrieve game roster, player
	shift times, generate the line combinations from each NHL game, and store all of 
	this in the database.
	
	-eventprocessor.py - special utility module that implements a class for downloading
	and storing data for the different 'event types' that occur during a game (shots, hits,
	blocks, goals)
	

Games:  Includes models and views for interacting with data on a "game" level.

	-models.py - Data models and methods for Teams, Players, Shift Times, and Lines. 
	
	-views.py - Not yet implemented
	

Teams:  Includes models and views for interacting with data on a "team" level.

	-models.py - Data model to represent each team in the league.
	
	-views.py - Not yet implemented
	
	
Players:  Includes models and views for interacting with data on a "player" level.
	
	-models.py - Data model to represent each player in the league.
	
	-views.py - Not yet implemented
	

	
	
Next Steps
----------
-Need to add a date field to the Game model.
-Currently only generating sets of 5 skaters on the ice.  This isn't particularly representative
of how lines work in hockey.  Need to further categorize lines into combinations of 3 forwards, 
2 defensemen, power play units, and penalty kill units.
-Known bug in line generating method.  We aren't calculating a new line when players 
come on the ice without replace another player going off the ice.  This can occur at 
the end of a penalty or at the end of a game when the goalie is pulled.  
-Need to implement testing structure across the board.  Unit tests, integration tests, etc.
-Need to be particularly careful and vigilent about confirming the data being downloaded 
to the database is correct and implement a rollback system in the event of failure.  
Unfortunately, we're forced to use data scraping on the NHL.com website to get this data, 
and the smallest of HTML changes on their end can ruin this whole operation.
-Implement a system to continuously scan the NHL games page and automatically download data
for new games as they occur.
-Views for each application
-Front end webpage design

