from django.contrib import admin
from datamanager.models import GameList

class GameListAdmin(admin.ModelAdmin):

	def test_actions(GameListAdmin, request, queryset):
		for g in queryset:
			g.load_game_data()

	test_actions.short_description = "Just a test action"

	actions = [test_actions]


admin.site.register(GameList, GameListAdmin)
