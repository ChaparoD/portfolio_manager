from django.contrib import admin

# Register your models here.
from .models import FactsDailyPrices, Asset, Portfolio

admin.site.register(Portfolio)
admin.site.register(Asset)
admin.site.register(FactsDailyPrices)