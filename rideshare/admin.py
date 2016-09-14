from django.contrib import admin

from .models import *

admin.site.register(Location)
admin.site.register(Event)


class RidersInline(admin.TabularInline):
	model = Rider

class StopsInline(admin.TabularInline):
	model = Stop

class RideAdmin(admin.ModelAdmin):
    inlines = [
        RidersInline, StopsInline,
    ]

admin.site.register(Ride, RideAdmin)
admin.site.register(Stop)
admin.site.register(Rider)