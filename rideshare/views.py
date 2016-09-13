import random, ast
from datetime import datetime, timedelta
from django.db.models import *
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
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

	def dispatch(self, request, *args, **kwargs):
		if Event.objects.count() == 1 : # il n'y a qu'un évènement
			event = Event.objects.first()
			return redirect('rideshare_ride_list', event.slug)
		else:
			return super(ListOfEvents, self).dispatch(request, *args, **kwargs)



#	@method_decorator(login_required, name='dispatch')
class EventRides(ListView):
	template_name = 'rideshare/ride_list.html'
	queryset = Ride.objects.filter(stop__isnull=False).annotate(
		number_of_riders=Count('rider'),
		remaining_seats=F('seats')-Count('rider'), # counts all riders?
		departure_datetime=Min('stop__time'),
		arrival_datetime=Max('stop__time'),
		)

	def get_context_data(self, **kwargs):
		context = super(EventRides, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = context['event'].name
		context['login_url'] = settings.LOGIN_URL
		return context



class RideDetail(DetailView):
	queryset = Ride.objects.filter(stop__isnull=False).annotate(
		number_of_riders=Count('rider'),
		remaining_seats=F('seats')-Count('rider'),
		departure_datetime=Min('stop__time'),
		arrival_datetime=Max('stop__time'),
		)

	def get_context_data(self, **kwargs):
		context = super(RideDetail, self).get_context_data(**kwargs)
		ride = Ride.objects.get(pk=self.kwargs['pk'])
		user_riders = Rider.objects.filter(ride=ride).exclude(user=None)
		context['users_who_are_riders'] = []
		for rider in user_riders :
			context['users_who_are_riders'].append(rider.user)
		return context


class CreateRide(LoginRequiredMixin, CreateView):
	model = Ride
	fields = ['seats', 'phone', 'price']
	login_url = settings.LOGIN_URL
	redirect_field_name = 'redirect_to'

	def get_context_data(self, **kwargs):
		context = super(CreateRide, self).get_context_data(**kwargs)
		context['event'] = Event.objects.get(slug=self.kwargs['slug']) 
		context['page_title'] = "Nouveau trajet : {}".format(context['event'].name)
		return context

	def post(self, request, *args, **kwargs):

		form = request.POST

		ride_type = form.get('ride_type')

		# Is this a Aller or Retour ?
		if ride_type == 'aller-retour' or ride_type == 'aller' : is_return = False
		elif ride_type == 'retour': is_return = True
		else :
			messages.error(request, "Une erreur a empêché la création de ce trajet. Si cela se reproduit, contactez moi.")
			redirect('rideshare_list_of_rides_for_event', slug=event.slug)

		event = get_object_or_404(Event, pk=form.get('event_id'))

		ride = Ride(
			event = event,
			owner = request.user,
			seats = form.get('seats'),
			price = form.get('price'),
			phone = form.get('phone'),
			is_return = is_return,
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

		if Stop.objects.filter(ride=ride):
			messages.success(request, "Félicitations, votre trajet a été créé !")
		else :
			messages.error(request, "Une erreur a empêché la création de ce trajet. Si cela se reproduit, contactez moi.")
			ride.delete()
			# TODO : cleanup this error and the one if the return radio isn't checked

		return redirect('rideshare_ride_detail', pk=ride.pk)


def JoinRide(request, pk):
	ride = get_object_or_404(Ride, pk=pk)
	if request.user.is_authenticated():
		user = request.user
		user_pk = user.pk
		if request.user == ride.owner :
			rider = Rider(ride=ride, user=user, name=user.get_full_name(), email=user.email, phone=ride.phone, message='', accepted=True)
			rider.save()
			return redirect('rideshare_ride_detail', pk=ride.pk)
	else :
		user_pk = ""
	return render(request, 'rideshare/ride_join_form.html', {'ride_pk': pk, 'user_pk': user_pk})


def CreateRider(request):
	form = request.POST
	ride = get_object_or_404(Ride, pk=form.get('ride_pk'))
	if form.get('user_pk'):
		user = get_object_or_404(User, pk=form.get('user_pk'))
		name = user.get_full_name()
		email = user.email
	else :
		user = None
		name = form.get('name')
		email = form.get('email')
	phone = form.get('phone')
	message = form.get('message')
	accepted = ride.owner == user # automatically accepts the request if the user is the ride owner
	if Rider.objects.filter(email=email).count() > 0 :
		if user and request.user == user :
			messages.info(request, 'Vous êtes déjà un des passagers ce covoiturage')
		else :
			messages.info(request, 'Ce passager participe déjà à ce covoiturage')
	elif not name or not email and not phone :
		messages.error(request, 'Il manque des informations pour créer ce passager.')
	else :
		if user and request.user == user or not user :
			rider = Rider(ride=ride, user=user, name=name, email=email, phone=phone, message=message, accepted=accepted)
			rider.save()
			if user : messages.success(request, 'Vous êtes désormais un passager de ce covoiturage')
			else : messages.success(request, name + ' est désormais un passager de ce covoiturage')
		else : 	messages.error("Vous n'êtes pas autorisé à faire cela.")
	return redirect('rideshare_ride_detail', pk=ride.pk)



def DeleteRider(request, pk):
	rider = get_object_or_404(Rider, pk=pk)
	if rider.ride.owner == request.user :
#		if form.get('message') :
#			explanation = '%0ASon message à votre attention:%0A<blockquote><i>{}</i></blockquote>'.format(form.get('message'))
		explanation = ''
		if request.user == rider.user :
			messages.success(request, "Vous n'êtes plus passager de ce covoiturage.")
		else :
			messages.success(request, "Ce passager a été retiré du covoiturage.")
		send_mail(
			'Votre voyage a été annulé !',
			'''Bonjour {},

			Malheureusement, votre covoiturage pour {} a été annulé par {}.
			{} 
			- L'équipe JDem'''.format(rider.name, rider.ride.event, rider.ride.owner.get_full_name(), explanation),
			settings.EMAIL_HOST_USER,
			[rider.email],
			fail_silently=False,
		)
		rider.delete()
	else :
		messages.error(request, "Vous n'êtes pas autorisé à modifier ce trajet.")
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)

def AcceptRider(request, pk):
	rider = get_object_or_404(Rider, pk=pk)
	ride = rider.ride
	if ride.rider_set.all().count() >= ride.seats :
		messages.error(request, "Ce covoiturage est déjà complet.")
	elif ride.owner != request.user :
		messages.error(request, "Vous n'êtes pas autorisé à modifier ce trajet.")
	elif rider.accepted :
		messages.info(request, "Cette demande a déjà été acceptée.")
	else :
		rider.accepted = True
		rider.save()
		messages.success(request, "Ce passager a été ajouté à votre covoiturage.")
		send_mail(
			'Votre demande de covoiturage a été acceptée !',
			'''Bonjour {}, votre demande de covoiturage {} a été acceptée {}. - L'équipe JDem'''.format(rider.email, rider.ride.event, rider.ride.owner.get_full_name()),
			settings.EMAIL_HOST_USER,
			[rider.email],
			fail_silently=False,
		) # TODO : accéder au trajet
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)

def DenyRider(request, pk):
	rider = get_object_or_404(Rider, pk=pk)
#	if form.get('message') :
#		explanation = '%0ASon message à votre attention:%0A<blockquote><i>{}</i></blockquote>'.format(form.get('message'))
#	else : explanation = ''
	explanation = ''
	messages.success(request, "Ce passager a été refusé.")
	send_mail(
		'Votre demande de covoiturage a été refusée',
		'''Bonjour {}, malheureusement, votre covoiturage pour {} n'a pas été acceptée par {}.{} - L'équipe JDem'''.format(rider.email, rider.ride.event, rider.ride.owner.get_full_name(), explanation),
		settings.EMAIL_HOST_USER,
		[rider.email],
		fail_silently=False,
	)
	rider.delete()
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)