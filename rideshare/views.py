import random, ast
from datetime import datetime, timedelta
from django.db.models import Count, F
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView

from .models import *
from .forms import *



#	@method_decorator(login_required, name='dispatch')
class ListOfEvents(ListView):
	model = Event

	def get_context_data(self, **kwargs):
		context = super(ListOfEvents, self).get_context_data(**kwargs)
		context['url_by_slug'] = True 
		return context



#	@method_decorator(login_required, name='dispatch')
class ListOfRides(ListView):
	template_name = 'ride_list.html'
	queryset = Ride.objects.annotate(remaining_seats=F('seats')-Count('rider'))

	def get_context_data(self, **kwargs):
		context = super(ListOfRides, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['event_slug']) 
		return context



#	@method_decorator(login_required, name='dispatch')
class DetailOfRide(DetailView):
	model = Ride
	template_name = 'ride_detail.html'

	def get_context_data(self, **kwargs):
		context = super(DetailOfRide, self).get_context_data(**kwargs)
		return context


