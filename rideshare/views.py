import random, ast
from datetime import datetime, timedelta
from django.db.models import *
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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
class EventRides(ListView):
	template_name = 'rideshare/ride_list.html'
	queryset = Ride.objects.filter(stop__isnull=False).annotate(
		number_of_riders=Count('rider'),
		remaining_seats=F('seats')-Count('rider'),
		departure_datetime=Min('stop__time'),
		arrival_datetime=Max('stop__time'),
		number_of_owned_rides=Max('stop__time')
		)

	def get_context_data(self, **kwargs):
		context = super(EventRides, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = context['event'].name
		context['login_url'] = settings.LOGIN_URL
		return context

def requestToJoinRide(request, pk):
	return JsonResponse({'requestSuccessful': 1})


class CreateNewRide(LoginRequiredMixin, CreateView):
	model = Ride
	fields = ['seats', 'price']
	login_url = settings.LOGIN_URL
	redirect_field_name = 'redirect_to'

	def get_context_data(self, **kwargs):
		context = super(CreateNewRide, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = "Nouveau trajet : {}".format(context['event'].name)
		return context

	def post(self, request, *args, **kwargs):

		form = request.POST

		ride_type = form.get('ride_type')

		if ride_type == 'go-and-return' :
			pass
		elif ride_type == 'just-go' :
			pass
		elif ride_type == 'just-return':
			pass
		else :
			# go back to the form
			pass


		event = get_object_or_404(Event, pk=form.get('event_id'))

		ride = Ride(
			event = event,
			owner = request.user,
			seats = form.get('seats'),
			price = form.get('price'),
			)
		ride.save()

		number_of_stops = form.get('number_of_stops')
		stop_labels = ['origin', 'destination'] # TODO : add "stop1", "stop2", ...

		for stop_label in stop_labels :

			# Register the location of this stop
			location, created = Location.objects.get_or_create(
				name = form.get(stop_label + '_place_name'),
				latitude = form.get(stop_label + '_place_latitude'),
				longitude = form.get(stop_label + '_place_longitude'),
				precision = form.get(stop_label + '_place_precision'),
				region = form.get(stop_label + '_place_region'),
				locality = form.get(stop_label + '_place_locality'),
				)

			time = (form.get(stop_label + '_date') + ' ' + form.get(stop_label + '_time')) # 22/08/2016 11:00:00
			time = datetime.strptime(time, '%d/%m/%Y %H:%M' )

			new_stop = Stop(
				ride = ride,
				location = location,
				time = time,
				)

			new_stop.save()

		return redirect('rideshare_list_of_rides_for_event', slug=event.slug)



#		<QueryDict: {
#	
#	'csrfmiddlewaretoken': ['KdGHVVhZOja96do8bRi6ZODFnYUQjswy7aa5z3KHprBFeAD8yPmYMuY94Aep1eIA'],
#	
#	'seats': ['5'],
#	'price': ['28'],
#	
#	'origin_place': ['Paris, France'],
#	'origin_place_name': ['Paris, France'],
#	'origin_place_latitude': ['48.856614'],
#	'origin_place_longitude': ['2.3522219'],
#	'origin_time': ['11:00:00'],
#	'origin_date': ['22/08/2016'],
#	'origin_place_precision': ['APPROXIMATE'],
#	
#	'destination_place': ['Pau, France'],
#	'destination_place_name': ['Pau, France'],
#	'destination_place_longitude': ['-0.370797'],
#	'destination_place_latitude': ['43.2951']
#	'destination_date': ['26/08/2016'],
#	'destination_time': ['14:00:00'],
#	'destination_place_precision': ['APPROXIMATE'],
#	
#	'id_return_radios': ['go-and-return'],
#	
#	
#	}>