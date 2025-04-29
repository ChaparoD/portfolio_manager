from django.db import transaction
from django.db.models import F
from ..models import Portfolio, Asset, RawDailyPrices, FactsDailyPrices,\
                     FactsDailyPricesSnapshot, AssetTransactions
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
        print(f'RaisedException during asset prices facts bulk operation :  {e} ')
    

def take_facts_snapshot(date):
    print("Snapshoting facts ... ... ..")
    snapshot = FactsDailyPrices.objects.all()
    bulk_facts_snapshot = []
    for facts in snapshot.iterator():
        bulk_facts_snapshot.append(FactsDailyPricesSnapshot(
                            date= facts.date,
                            asset= facts.asset,
                            price= facts.price,
                            asset_value = facts.asset_value,
                            snapshot_date= date))
    try:
        with transaction.atomic():
            FactsDailyPricesSnapshot.objects.bulk_create(bulk_facts_snapshot)
    except Exception as e:
        print(f'RaisedException during snapshot fact asset prices bulk operation :  {e} ')
    
def save_transactions(date, transactions):
    print("Saving transactions ... ... ..")
    bulk_transactions = []
    for data in transactions:
        bulk_transactions.append(AssetTransactions(
                            date = date,
                            action = data['action'],
                            amount = data['amount'],
                            asset = data['asset'],
                            portfolio = data['portfolio']
                            ))
    try:
        with transaction.atomic():
            AssetTransactions.objects.bulk_create(bulk_transactions)
    except Exception as e:
        print(f'RaisedException during transactions bulk operation :  {e} ')
    pass

"""
[{'date': '2025-04-02', 'action': 'Buy', 'amount': '20000', 'portfolio': 'portafolio 1', 'asset': 'Europa'},
 {'date': '2025-04-02', 'action': 'Buy', 'amount': '234512451', 'portfolio': 'portafolio 1', 'asset': 'ABS'}]
"""
def update_facts_assets_values(min_date, transactions):
    facts_domain = FactsDailyPrices.objects.filter(date=min_date)
    if not facts_domain:
        print("No facts to update")
        return
    else:
        assets = Asset.objects.all().select_related('portfolio')
        for mov in transactions:
            """
            Para cada transacción, si existe el activo relacionado, calcula la nueva cantidad
            obs:
            - Falta cubrir casos de si el activo no existe para el portafolio
            - No hay validaciones de venta por sobre lo disponible
            """
            asset = assets.get(name = mov["asset"], portfolio__name = mov["portfolio"] )
            if asset:
                asset_transaction_price = facts_domain.filter(date=min_date, asset = asset).values('price')
                if asset["action"] == "Sell":
                    asset.quantity = max(0, asset.quantity - float(mov["amount"]) / 
                                         asset_transaction_price[0]['price'])
                else:
                    asset.quantity += float(mov["amount"])/asset_transaction_price[0]['price'] 
                
                asset.save()
                facts_domain.filter(asset=asset).update(asset_value = F('price') *asset.quantity )



        