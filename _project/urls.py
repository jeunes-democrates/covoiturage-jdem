from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView

admin.site.site_header = 'Covoiturage JDem - Administration'

urlpatterns = [
	url('^', include('django.contrib.auth.urls')), # keeping this for the logout feature
	url(r'^auth/', include('django_auth_network_client.urls')),
	url(r'^arriere-boutique/', admin.site.urls, name='admin'),
	url(r'^covoiturage/', include('rideshare.urls')),
	url(r'^$', RedirectView.as_view(url="/covoiturage/", permanent=False)),
]