from django.contrib import admin, messages
from datamanager.models import GameHeader

class GameHeaderAdmin(admin.ModelAdmin):

	def load_game(GameListAdmin, request, queryset):
		'''
		Load full shift data for selected games.  This function runs a lot 
		of data processes and takes a long time to execute.  Also too 
		closely linked to the data layer for comfort, so I will need to 
		reconsider implementation.  For now it's a quick and easy interface 
		for running the meaty data guts of this project'''

		for g in queryset:
			if g.processed == True:
				messages.error(request, "%d has already been processed" % g.pk)
				return
		for g in queryset:
			g.load_game_data()

	actions_on_top = True
	actions_on_bottom = True
	list_display = ('__unicode__','processed',)
	list_editable = ()

	load_game.short_description = "Load game to database"

	actions = [load_game,]

admin.site.register(GameHeader, GameHeaderAdmin)
