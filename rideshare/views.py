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
from django.utils.html import strip_tags
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView

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
		context['page_title'] = "Détail du trajet"
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
			messages.error(request, "Une erreur a empêché la création de ce trajet.")
			redirect('rideshare_ride_list', slug=event.slug)

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
				greetingcision = form.get(stop_label + '_place_greetingcision'),
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



class UpdateRide(LoginRequiredMixin, UpdateView):
	model = Ride
	fields = ['seats', 'price', 'phone', 'message']
	template_name = 'form.html'

	def get_context_data(self, **kwargs):
		context = super(UpdateRide, self).get_context_data(**kwargs)
		context['page_title'] = "Modifier mon trajet"
		return context

	def get_success_url(self):
		return reverse('rideshare_ride_detail', kwargs={'pk':self.object.pk})


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
	return render(request, 'rideshare/ride_join_form.html', {'ride_pk': pk, 'user_pk': user_pk, 'page_title': 'Nouveau passager'})



#
# EMAIL PREFIX AND SUFFIX
#

def email_greeting(request):
	return  "Bonjour {},".format(request.user.get_full_name())

def email_signature(request):
	return "- L'équipe JDem"



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
	if Rider.objects.filter(ride=ride.pk, email=email).count() > 0 :
		if user and request.user == user :
			messages.info(request, 'Vous êtes déjà un des passagers ce covoiturage')
		else :
			messages.info(request, 'Ce passager participe déjà à ce covoiturage')
	elif not name or not email and not phone :
		messages.error(request, 'Il manque des informations pour ajouter ce passager.')
	else :
		if user and request.user == user or not user :
			rider = Rider(ride=ride, user=user, name=name, email=email, phone=phone, message=message, accepted=accepted)
			rider.save()
			if accepted == False : # si la demande est auto acceptée, c'est que le covoitureur a fait la demande pour lui-même
				send_mail(
					subject='Votre demande de covoiturage a été enregistrée',
					message='''
						{greeting} votre demande pour rejoindre le covoiturage {ride_url} a été enregistrée. Elle devra être validée {ride_owner}. {signature}
						'''.format(
							greeting=email_greeting(request),
							ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
							ride_owner=ride.owner.get_full_name(),
							signature=email_signature(request),
							),
					html_message='''
						<p>{greeting},</p>
						<p>Votre demande pour rejoindre le covoiturage {ride_url} a été enregistrée. Elle devra être validée {ride_owner}.</p>
						<p>{signature}</p>
						'''.format(
							greeting=email_greeting(request),
							ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
							ride_owner=ride.owner.get_full_name(),
							signature=email_signature(request),
							),
					recipient_list=[rider.email,],
					from_email=settings.DEFAULT_FROM_EMAIL,
					fail_silently=False,
				)
				messages.info(request, 'Votre demande a bien été enregistrée, et le covoitureur en a été averti.')
			else :
				messages.success('Vous êtes désormais un passager de ce covoiturage.')
		else :
			messages.error("Vous n'êtes pas autorisé à faire cela.")
	return redirect('rideshare_ride_detail', pk=ride.pk)



@login_required
def DeleteRider(request, pk):
	rider = get_object_or_404(Rider, pk=pk)
	ride = rider.ride
	if ride.owner == request.user :
#		if form.get('message') :
#			explanation = '%0ASon message à votre attention:%0A<blockquote><i>{}</i></blockquote>'.format(form.get('message'))
#		explanation = ''
#		TODO : add support for explaining why rider was kicked out
		send_mail(
			subject='Votre demande de covoiturage a été annulée !',
			message='''
				{greeting} votre covoiturage {ride_url} a été annulé par {ride_owner}. Vous pouvez réaliser une nouvelle demande de covoiturage. {signature}
				'''.format(
					greeting=email_greeting(request),
					ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
					ride_owner=ride.owner.get_full_name(),
					signature=email_signature(request),
					), # TODO : also trigger this on ride cancellation
			html_message='''
				<p>{greeting},</p>
				<p>Votre covoiturage {ride_url} a été annulé par {ride_owner}. Vous pouvez réaliser une nouvelle demande de covoiturage.</p>
				<p>{signature}</p>
				'''.format(
					greeting=email_greeting(request),
					ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
					ride_owner=ride.owner.get_full_name(),
					signature=email_signature(request),
					),
			recipient_list=[rider.email,],
			from_email=settings.DEFAULT_FROM_EMAIL,
			fail_silently=False,
		)
		rider.delete()
		if request.user == rider.user :
			messages.success(request, "Vous n'êtes plus passager de ce covoiturage.")
		else :
			messages.success(request, "Ce passager a été retiré du covoiturage.")
	else :
		messages.error(request, "Vous n'êtes pas autorisé à modifier ce trajet.")
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)


#TODO : add support for cancelling rides

@login_required
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
		messages.success(request, "Ce passager a été ajouté à votre covoiturage, et un message de confirmation lui a été adressé.")
		send_mail(
			subject='Votre demande de covoiturage a été acceptée !',
			message='''
				{greeting} votre demande pour rejoindre le covoiturage {ride_url} a été acceptée par {ride_owner}. {signature}
				'''.format(
					greeting=email_greeting(request),
					ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
					ride_owner=ride.owner.get_full_name(),
					signature=email_signature(request),
					),
			html_message='''
				<p>{greeting},</p>
				<p>Votre demande pour rejoindre le covoiturage {ride_url} a été acceptée par {ride_owner}.</p>
				<p>{signature}</p>
				'''.format(
					greeting=email_greeting(request),
					ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
					ride_owner=ride.owner.get_full_name(),
					signature=email_signature(request),
					),
			recipient_list=[rider.email,],
			from_email=settings.DEFAULT_FROM_EMAIL,
			fail_silently=False,
		)
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)



@login_required
def DenyRider(request, pk):
	rider = get_object_or_404(Rider, pk=pk)
	ride = rider.ride
#	if form.get('message') :
#		explanation = '%0ASon message à votre attention:%0A<blockquote><i>{}</i></blockquote>'.format(form.get('message'))
#	else : explanation = ''
#	explanation = ''
	send_mail(
		subject='Votre demande de covoiturage a été rejetée',
		message='''
			{greeting} votre demande pour rejoindre le covoiturage {ride_url} a malheureusement été rejetée par {ride_owner}. Vous pouvez réaliser une nouvelle demande de covoiturage. {signature}
			'''.format(
				greeting=email_greeting(request),
				ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
				ride_owner=ride.owner.get_full_name(),
				signature=email_signature(request),
				),
		html_message='''
			<p>{greeting},</p>
			<p>Votre demande pour rejoindre le covoiturage {ride_url} a malheureusement été rejetée par {ride_owner}.</p>
			<p>Vous pouvez réaliser une nouvelle demande de covoiturage.</p>
			<p>{signature}</p>
			'''.format(
				greeting=email_greeting(request),
				ride_url= request.build_absolute_uri(reverse('rideshare_ride_detail', args=[ride.pk,])),
				ride_owner=ride.owner.get_full_name(),
				signature=email_signature(request),
				),
		recipient_list=[rider.email,],
		from_email=settings.DEFAULT_FROM_EMAIL,
		fail_silently=False,
	)
	rider.delete()
	messages.success(request, "Ce passager a été refusé.")
	return redirect('rideshare_ride_detail', pk=rider.ride.pk)



def SendTestEmail(request):
	if request.user.is_staff and settings.DEBUG == True :
		send_mail(
			subject='Mail test pour Antonin !',
			message='''
				{greeting} votre email en texte clair a bien été envoyé. {signature}
				'''.format(
					greeting=email_greeting(request),
					signature=email_signature(request),
					),
			html_message='''
				<p>{greeting},</p>
				<p>Votre email en HTML a bien été envoyé.</p>
				<p>{signature}</p>
				'''.format(
					greeting=email_greeting(request),
					signature=email_signature(request)
					),
			recipient_list=['antonin.grele@gmail.com',],
			from_email=settings.DEFAULT_FROM_EMAIL,
			fail_silently=False,
		)
		messages.success(request, 'Email correctement envoyé !')
	return redirect('rideshare_event_list')