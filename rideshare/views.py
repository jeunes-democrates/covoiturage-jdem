import random, ast
from datetime import datetime, timedelta
from django.db.models import F, ExpressionWrapper, Count, Min, Max, DecimalField
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView

from .models import *
from .forms import *



#	@method_decorator(login_required, name='dispatch')
class ListOfEvents(ListView):
	template_name = 'list.html'
	model = Event

	def get_context_data(self, **kwargs):
		context = super(ListOfEvents, self).get_context_data(**kwargs)
		context['url_by_slug'] = True
		context['page_title'] = "Prochains évènements"
		return context



#	@method_decorator(login_required, name='dispatch')
class ListOfRides(ListView):
	template_name = 'rideshare/ride_list.html'
	queryset = Ride.objects.annotate(
		number_of_riders=Count('rider'),
		remaining_seats=F('seats')-Count('rider'),
		departure_datetime=Min('stop__time'),
		arrival_datetime=Max('stop__time'),
		)

	def get_context_data(self, **kwargs):
		context = super(ListOfRides, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = context['event'].name
		return context

def requestToJoinRide(request, pk):
	return JsonResponse({'requestSuccessful': 1})


class CreateNewRide(CreateView):
	model = Ride
	fields = ['seats', 'price']

	def get_context_data(self, **kwargs):
		context = super(CreateNewRide, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = "Nouveau trajet : {}".format(context['event'].name)
		return context