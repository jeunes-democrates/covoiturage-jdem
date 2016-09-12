from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
	url(r'^$', views.Register.as_view(), name='register'),
]