from django.contrib import admin, messages
from datamanager.models import GameList

class GameListAdmin(admin.ModelAdmin):

	def test_actions(GameListAdmin, request, queryset):
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

	test_actions.short_description = "Load game to database"


	actions = [test_actions,]


admin.site.register(GameList, GameListAdmin)
