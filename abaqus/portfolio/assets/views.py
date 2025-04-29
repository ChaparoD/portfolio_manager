from django.shortcuts import render
from .models import FactsDailyPrices, Asset, Portfolio
from django.views import View
from django.http import  JsonResponse
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from .serializers import  UserSerializer, AssetWeightSerializer
from datetime import datetime
from django.db.models import Sum



""" HTML Redirections"""
def portfolio_time_series(request):
    # URL del endpoint
    
    return render(request, 'assets/portfolios.html')


def asset_weights(request):
    return render(request, 'assets/assetsWeights.html')

"""Recieve 1 or more Transactions"""
def transaction_view(request):
    if request.method == 'POST':
        transactions = request.POST.getlist('transactions')
        print("llego post")
        return JsonResponse({'status': 'success', 'transactions': transactions})
    return render(request, 'assets/transaction_form.html')


""" Helpers"""
def get_porfolio_values(asset_values):
    response_data = []
    portfolio_values = asset_values.values('date', 
                                               'asset__portfolio__id')\
                                .annotate(portfolio_daily_value=Sum('asset_value'))
    
    portfolio_ids = portfolio_values.values('asset__portfolio__id').distinct()
    for portfolio in portfolio_ids:
        portfolio_id = portfolio['asset__portfolio__id']
        values = portfolio_values.filter(asset__portfolio__id = portfolio_id)
        portfolio_name = Portfolio.objects.get(id=portfolio_id).name
        portfolio_data = {
        "portfolio_id" : portfolio_id,
        "portfolio_name": portfolio_name,
        "total_values": [{"date": value['date'].strftime('%Y-%m-%d'),
                        "value": value['portfolio_daily_value']} for value in values]
        }
        response_data.append(portfolio_data)

    return response_data

def get_portfolio_daily_value(values ,portfolio_id, date):
            return values[portfolio_id].get(date, None)

""" REST framework views"""
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class AssetWeightViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = FactsDailyPrices.objects.all().select_related('asset').order_by('date')
    serializer_class = AssetWeightSerializer
    permission_classes = [permissions.IsAuthenticated]



""" Assets Weights endpoint """
class AssetWeight(View):
        
    def get(self, request):
        start_date = request.GET.get('fecha_inicio')
        end_date = request.GET.get('fecha_fin')

        if not start_date or not end_date:
            return JsonResponse({"error": "fecha_inicio and fecha_fin are required"}, status=400)
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({"error": "Invalid date format"}, status=400)

        
        asset_values = FactsDailyPrices.objects.filter(date__range=(start_date, end_date))\
                                    .select_related('asset')\
                                    .prefetch_related('asset__portfolio')\
                                    .values('date','asset_id', 'asset_value','asset__name', 
                                            'asset__portfolio__id','asset__portfolio__name')
        
        portfolio_values = asset_values.values('date', 'asset__portfolio__id')\
                                .annotate(portfolio_daily_value=Sum('asset_value'))\
                                .values_list('asset__portfolio__id', 
                                             'date', 
                                             'portfolio_daily_value')

        # Almacenamos valores de portafolios en memoria para optimizar los llamados en el cálculo de "weight"
        portfolio_dict_values = {}  # {"portfolio_id" : {"date" : "value"}}
        for item in portfolio_values:
            portfolio_id = item[0]
            if portfolio_id not in portfolio_dict_values:
                portfolio_dict_values[portfolio_id] = {}
            portfolio_dict_values[portfolio_id][item[1].strftime('%Y-%m-%d')] = item[2]
       
        response_data = {
            "fecha_inicio": start_date.strftime('%Y-%m-%d'),
            "fecha_fin": end_date.strftime('%Y-%m-%d'),
            "registers": len(asset_values), 
            "assets": []
            }

        for asset in asset_values:

            asset_id = asset['asset_id']
            portfolio_id = asset['asset__portfolio__id']
            values = asset_values.filter(asset_id=asset_id).values('date', 'asset_value')
            asset_data = {
                "asset_id": asset_id,
                "asset_name": asset["asset__name"],
                "portfolio_name": asset["asset__portfolio__name"],
                "weights": [{"date": value['date'].strftime('%Y-%m-%d'),
                            "weight": round(value['asset_value']/
                                portfolio_dict_values[portfolio_id][value['date'].strftime('%Y-%m-%d')]
                                            , ndigits=3)
                            } for value in values]
            }
            response_data["assets"].append(asset_data)

        return JsonResponse(response_data)



""" Portfolio values endpoint"""
class PortfolioValues(View):

    def get(self, request):

        start_date = request.GET.get('fecha_inicio')
        end_date = request.GET.get('fecha_fin')

        if not start_date or not end_date:
            return JsonResponse({"error": "fecha_inicio and fecha_fin are required"}, status=400)
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({"error": "Invalid date format"}, status=400)

        
        asset_values = FactsDailyPrices.objects.filter(date__range=(start_date, end_date))\
                                    .select_related('asset')\
                                    .prefetch_related('asset__portfolio')\
                                    .values('date','asset_id', 'asset_value',
                                            'asset__name',
                                            'asset__portfolio',
                                            'asset__portfolio__name')
        response_data = {
            "fecha_inicio": start_date.strftime('%Y-%m-%d'),
            "fecha_fin": end_date.strftime('%Y-%m-%d'),
            "portfolios": []
            }

        response_data["portfolios"] = get_porfolio_values(asset_values)

        return JsonResponse(response_data)


""" Portfolio Options"""
class PortfolioOptions(View):
    def get(self, request):
        portfolio_names = list(Portfolio.objects.all().values_list('name', flat=True))
        return JsonResponse({'portfolios': portfolio_names}, safe=False)
    
    #CRUD se completa aquí.

class AssetOptions(View):
    def get(self, request):
        assets_names = list(Asset.objects.all().values_list('name', flat=True).distinct())
        return JsonResponse({'assets': assets_names}, safe=False)
    
    #CRUD se completa aquí.


