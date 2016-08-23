# -*- coding: utf-8 -*-
import os, datetime
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
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
	owner = models.ForeignKey(User)
	seats = models.SmallIntegerField(default=5)
#	return_ride = models.ForeignKey('self', null=True, blank=True)
	is_return = models.BooleanField(default=False)
	price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
	# cost is divided equally among users

	def __str__(self):
		return '{} {} — {} seats'.format(self.owner.first_name, self.owner.last_name, str(self.seats))



class Stop(models.Model):
	ride = models.ForeignKey(Ride)
	location = models.ForeignKey(Location)
	time = models.DateTimeField()

	def __str__(self):
		return '{} — {} — {}'.format(self.ride, self.location.name, self.time)

	class Meta:
		ordering = ('time',)


class Rider(models.Model):
	ride = models.ForeignKey(Ride)
	user = models.ForeignKey(User, null=True, blank=True)
	status = models.CharField(max_length=32, choices=(
		('PENDING', 'demande de participation au trajet en attente de confirmation'),
		('CONFIRMED', 'demande de participation au trajet validée'),
		('CANCELLED', 'demande de participation au trajet annulée'),
		('TIMED_OUT', 'demande de participation au trajet expirée'),
		), default='PENDING')
	joining_stop = models.ForeignKey(Stop, related_name='joining_rider')
	leaving_stop = models.ForeignKey(Stop, related_name='leaving_rider')
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return '{}, from {} to {}, riding with {}'.format(
			self.user.username,
			self.joining_stop.location.name,
			self.leaving_stop.location.name,
			self.ride
			)

	def confirm(self):
		self.status = CONFIRM
		self.save()

	def unconfirm(self):
		self.status = PENDING
		self.save()

	def cancel(self):
		self.status = CANCELLED
		self.save()

	def timeout(self):
		self.status = TIMED_OUT
		self.save()

	def has_expired(self):
		expiration_time = settings.RIDESHARE_REQUEST_EXPIRATION_TIME
		if self.created + timedelta(hours=expiration_time) > datetime.now() :
			self.timeout()
			return True
		else :
			return False
