from django.db import models

# Create your models here.

class Team(models.Model):
	name = models.CharField(max_length = 100)
	initials = models.CharField(max_length = 3)

	def __unicode__(self):
		return self.name