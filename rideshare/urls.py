from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
	url(r'^events/(?P<slug>[\x00-\x7F]+)/create-new-ride/$', views.CreateRide.as_view(), name='rideshare_ride_create'),
	url(r'^events/(?P<slug>[\x00-\x7F]+)/$', views.EventRides.as_view(), name='rideshare_ride_list'),
	url(r'^events/$', views.ListOfEvents.as_view(), name='rideshare_event_list'),
	url(r'^rides/(?P<pk>[0-9]+)/$', views.RideDetail.as_view(), name='rideshare_ride_detail'),
	url(r'^rides/(?P<pk>[0-9]+)/join/$', views.JoinRide, name='rideshare_join_ride'),
	url(r'^rides/(?P<pk>[0-9]+)/update/$', views.UpdateRide.as_view(), name = 'rideshare_ride_update'),
	url(r'^rider/new/$', views.CreateRider, name='rideshare_rider_create'),
	url(r'^rider/(?P<pk>[0-9]+)/accept/$', views.AcceptRider, name='rideshare_rider_accept'),
	url(r'^rider/(?P<pk>[0-9]+)/deny/$', views.DenyRider, name='rideshare_rider_deny'),
	url(r'^rider/(?P<pk>[0-9]+)/delete/$', views.DeleteRider, name='rideshare_rider_delete'),
	url(r'^email/$', views.SendTestEmail, name='rideshare_send_test_email'),
	url(r'^$', RedirectView.as_view(url="events", permanent=False)),
]