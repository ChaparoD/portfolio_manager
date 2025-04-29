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
    Modelo dimensional de hechos:
    - Se agregará cada registro de Raw (tiempo/activo/precio) por cuantas "Instancias" 
        encuentre de ese activo particular en los portfolios.
        Ej: Si todas las acciones están en ambos portafolios, se Facts tiene el doble de
          registros que Raw. 
    NOTE : Se pueden entregar vistas de consumo del modelo para usuarios no expertos en SQL.
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
    

def update_facts_assets_values(min_date, transactions):
    print("Updating Facts ... ... ..")
    facts_domain = FactsDailyPrices.objects.filter(date__gte=min_date)
    if not facts_domain:
        print("No facts to update")
        return
    else:
        assets = Asset.objects.all().select_related('portfolio')
        print(transactions)
        for mov in transactions:
            """
            Para cada transacción, si existe el activo relacionado, calcula la nueva cantidad, valor
            asociado
            obs:
            - Falta cubrir casos de si el activo no existe para el portafolio.
            - No hay validaciones de venta por sobre lo disponible. Solo se lleva cantidad y valor a 0
            - No existen agrupaciones bajo transacciones sobre el mismo activo.
            """
            asset = assets.get(name = mov["asset"], portfolio__name = mov["portfolio"] )
            if asset:
                asset_transaction_price = facts_domain.filter(date=min_date, asset = asset).values('price')
                if asset_transaction_price:
                    if mov["action"] == "Sell":
                        asset.quantity = round(max(0, asset.quantity - float(mov["amount"]) / 
                                            asset_transaction_price[0]['price']), 3)
                    else:
                        asset.quantity += round(float(mov["amount"])/asset_transaction_price[0]['price'], 3) 
                    
                    asset.save()
                    facts_domain.filter(asset=asset).update(asset_value = 
                                                         F('price') * asset.quantity) 
                    



        