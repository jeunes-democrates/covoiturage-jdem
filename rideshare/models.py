# -*- coding: utf-8 -*-
import os, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.utils.text import slugify
from datetime import datetime, timedelta



class Location(models.Model):
	name = models.CharField(max_length=48)
	region = models.CharField(max_length=255, default="Île-de-France") # "Île-de-France", "Bretagne"
	locality = models.CharField(max_length=255, default="Paris") # "Paris", "Guidel"
	latitude = models.DecimalField(max_digits=8, decimal_places=6)
	longitude = models.DecimalField(max_digits=8, decimal_places=6)
	precision = models.CharField(max_length=48) # based on google maps api precision

	def __str__(self):
		#Format as :  Guidel (23.029923, 83,282193)
		return "{} — [{}, {}]".format(self.name, self.latitude, self.longitude)



class Event(models.Model):
	name = models.CharField(max_length=48, unique=True)
	slug = models.SlugField(max_length=48, unique=True)
	description = models.CharField(max_length=5000)
	location = models.ForeignKey(Location)
	start_date = models.DateTimeField(default=datetime.now)
	end_date = models.DateTimeField(default=datetime.now)

	def __str__(self):
		return self.name



class Ride(models.Model):
	event = models.ForeignKey(Event)
	owner = models.ForeignKey(User, related_name="owned_ride")
	phone = models.CharField(max_length=32, default="00 00 00 00 00")
	riders = models.ManyToManyField(User, through="Rider", related_name="ride")
	seats = models.SmallIntegerField(default=5)
#	return_ride = models.ForeignKey('self', null=True, blank=True)
	is_return = models.BooleanField(default=False)
	price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
	# cost is divided equally among users

	def __str__(self):
		return '[{}] {} {}'.format(
			self.pk,
			self.owner.first_name,
			self.owner.last_name,
			)



class Stop(models.Model):
	ride = models.ForeignKey(Ride)
	location = models.ForeignKey(Location)
	time = models.DateTimeField()

	def __str__(self):
		return '{} — {} — {}'.format(self.ride, self.location.name, self.time)

	class Meta:
		ordering = ('time',)


class Rider(models.Model):
	ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
	user = models.ForeignKey(User, null=True, blank=True)
#	joining_stop = models.ForeignKey(Stop, related_name='joining_rider') TODO : use these
#	leaving_stop = models.ForeignKey(Stop, related_name='leaving_rider')
	name = models.CharField(max_length=64, default="No Name")
	email = models.EmailField(default="no@email.com")
	phone = models.CharField(max_length=32, default="00 00 00 00 00")
	message = models.CharField(max_length=255, null=True, blank=True)
	accepted = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return '[{}] {}, riding with {}'.format(
			self.pk,
			self.user.first_name + ' ' + self.user.last_name,
			self.ride.owner.first_name + ' ' + self.ride.owner.last_name
			)

	def accept(self):
		self.accepted = True
		self.save()