from django.contrib import admin

from .models import Activity, Expense, Trip

admin.site.register(Trip)
admin.site.register(Activity)
admin.site.register(Expense)
