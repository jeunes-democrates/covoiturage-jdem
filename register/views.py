import random, ast
from datetime import datetime, timedelta
from django.db.models import *
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
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
from django.views.generic.edit import CreateView, FormView

#from .models import *
from .forms import *



#	@method_decorator(login_required, name='dispatch')
class Register(FormView):
	template_name = 'registration/registration_form.html'
	model = User
	form_class = RegistrationForm
	success_url = '/login'

	def form_valid(self, form):
		first_name = form.cleaned_data['first_name']
		last_name = form.cleaned_data['last_name']
		email = form.cleaned_data['email']
		password = form.cleaned_data['password']
		existing_user_with_this_email = User.objects.filter(email=email)
		if existing_user_with_this_email :
			messages.info(self.request, 'Un compte est déjà enregistré à cette adresse. Vous pouvez directement vous connecter.')
		else :
			User.objects.create_user(
				username = email,
				email = email,
				password = password,
				first_name = first_name,
				last_name = last_name,
				)
			user = authenticate(username=email, password=password)
			if user is not None: login(self.request, user)
			messages.success(self.request, 'Votre compte a été créé, et vous êtes désormais connecté(e).')
			return redirect('rideshare_event_list')
		return super(Register, self).form_valid(form)