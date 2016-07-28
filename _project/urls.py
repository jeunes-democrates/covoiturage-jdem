from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

admin.site.site_header = 'Covoiturage JDem - Administration'

urlpatterns = [
	url('^', include('django.contrib.auth.urls')),
	url(r'^arriere-boutique/', admin.site.urls, name='admin'),
	url(r'^covoiturage/', include('rideshare.urls')),
	url(r'^$', RedirectView.as_view(url="/covoiturage", permanent=False)),
]