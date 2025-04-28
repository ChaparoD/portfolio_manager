from django.db import transaction
from ..models import Portfolio, Asset, RawDailyPrices, FactsDailyPrices
import polars as pl
import os, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR, 'data/datos.xlsx')

def extract_instances():
    print("Creating Instances ... ... ..")
    weights = pl.read_excel(file_path, sheet_name="weights")

    port_counter = len(weights.columns)-2
    portfolios_names = [weights.columns[2:][port] for port in range(port_counter)]
    
    for portfolio in portfolios_names:
        try:
            with transaction.atomic():
                new_portfolio = Portfolio.objects.create(name=portfolio, 
                                                         initial_value = 1000000000)
                new_portfolio.save() 
        except Exception as e:
                print(f'RaisedException during portfolio creation:  {e} ')
                
        else:
            new_portfolio_assets = weights.select('activos', portfolio)
            for assets in new_portfolio_assets.iter_rows():
                if assets[1]:
                    try:
                        with transaction.atomic():
                            new_asset = Asset.objects.create(name = assets[0], 
                                                portfolio=new_portfolio, 
                                                initial_weight = round(assets[1], 3) )
                            new_asset.save()

                    except Exception as e:
                        print(f'RaisedException during asset creation:  {e} ')




def calculate_quantity(df :pl.DataFrame):
    asset_names = df.columns[1:]
    for asset_name in asset_names:
        query_set = Asset.objects.filter(name=asset_name).select_related('portfolio')

        for instance in query_set:
            
            qty = (instance.initial_weight * instance.portfolio.initial_value)/df[asset_name][0]
            instance.update_quantity(round(qty, 3))


def load_raw_prices():
    print("Loading Prices ... ... ..")

    asset_prices = pl.read_excel(file_path, sheet_name="Precios")
    calculate_quantity(asset_prices.slice(0, 1))
    assets_names, asset_number, bulk_data =asset_prices.columns, asset_prices.width , []

    for value in asset_prices.iter_rows():
        for asset in range(1, asset_number):
            bulk_data.append(RawDailyPrices(
                                date=value[0],
                                asset_name=assets_names[asset],
                                price=round(value[asset], 3) ))
            

    try:
        with transaction.atomic():
            RawDailyPrices.objects.bulk_create(bulk_data)
    except Exception as e:
        print(f'RaisedException during asset prices bulk operation :  {e} ')

    
def transform_prices():
    """
    Dimensional fact model will have, as many duplicated raw rows
    exists for each portfolio instance.
    So, for every Asset Price, if the Asset has presence in 3  Portfolios, then 3 rows will 
    be added, with their corresponding weight.
    NOTE : SQL precise views of could be constructed to ease the access for non SQL experts.
    """
    print("Conforming facts ... ... ..")
    raw_prices = RawDailyPrices.objects.all()
    bulk_facts = []
    for price in raw_prices.iterator():
        related_assets = Asset.objects.filter(name = price.asset_name)
        for asset in related_assets:
            bulk_facts.append(FactsDailyPrices(
                                date= price.date,
                                asset= asset,
                                price= price.price,
                                asset_value = round(price.price * asset.quantity, 3) ))
    try:
        with transaction.atomic():
            FactsDailyPrices.objects.bulk_create(bulk_facts)
    except Exception as e:
        print(f'RaisedException during asset prices bulk operation :  {e} ')
    