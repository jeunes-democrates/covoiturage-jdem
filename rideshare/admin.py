from django.contrib import admin

from .models import *

admin.site.register(Location)
admin.site.register(Event)
admin.site.register(Ride)
admin.site.register(Stop)
admin.site.register(Rider)