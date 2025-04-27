from django.db import models

# Create your models here.
class Portfolio(models.Model):

    name = models.CharField(max_length=100, unique=True)
    initial_value = models.FloatField()

    class Meta:
        db_table = 'dim_portafolio'

    

class Asset(models.Model):

    name = models.CharField(max_length=100)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    initial_weight = models.FloatField()
    quantity = models.FloatField(default="0")

    class Meta:
        db_table = 'dim_asset'
        unique_together = ('name', 'portfolio')

    
    def update_quantity(self, new_quantity):
        self.quantity = new_quantity
        self.save()


class RawDailyPrices(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateField()
    asset_name = models.CharField()
    price = models.FloatField()

    class Meta:
        db_table = 'raw_daily_prices'
        unique_together = ('date', 'asset_name')

class FactsDailyPrices(models.Model):

    date = models.DateField()
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    price = models.FloatField()
    asset_value = models.FloatField()

    class Meta:
        db_table = 'facts_daily_prices'
        unique_together = ('date', 'asset')
