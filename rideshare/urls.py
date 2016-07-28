from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
	url(r'^events/(?P<event_slug>[\x00-\x7F]+)/$', views.ListOfRides.as_view(), name='rideshare_list_of_rides_for_event'),
	url(r'^events/$', views.ListOfEvents.as_view(), name='rideshare_list_of_events'),
	url(r'^ride/(?P<ride_pk>[0-9]+)/$', views.DetailOfRide.as_view(), name='ride_share_detail_of_ride'),
	url(r'^$', RedirectView.as_view(url="events", permanent=False)),
]