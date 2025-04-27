from django.shortcuts import render
from .models import FactsDailyPrices, Asset, Portfolio
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from .serializers import GroupSerializer, UserSerializer, AssetWeightSerializer
from datetime import datetime
from django.db.models import Sum


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


def home(request):

    return render(request, "assets/home.html", {})


class AssetWeightViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = FactsDailyPrices.objects.all().select_related('asset').order_by('date')
    serializer_class = AssetWeightSerializer
    permission_classes = [permissions.IsAuthenticated]

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
                                .annotate(portfolio_daily_value=Sum('asset_value'))
        
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
                            "weight": (value['asset_value']/
                                         portfolio_values.filter(asset__portfolio__id = portfolio_id,
                                                                  date= value['date'])\
                                         .values('portfolio_daily_value')[0]['portfolio_daily_value']
                                         ) } for value in values]
            }
            response_data["assets"].append(asset_data)

        return JsonResponse(response_data)



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

