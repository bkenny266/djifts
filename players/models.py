'''
PLAYER - models.py
'''

from django.db import models

# Create your models here.
class Player(models.Model):
	first_name = models.CharField(max_length = 255)
	last_name = models.CharField(max_length = 255)
	position = models.CharField(max_length = 2)
	number = models.IntegerField()

	def __unicode__(self):
		return self.last_name + ", " + self.first_name
