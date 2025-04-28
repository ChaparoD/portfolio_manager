from django.urls import path, include
from assets import views
from .views import AssetWeight, PortfolioValues, PortfolioOptions
from rest_framework import routers
from .views import UserViewSet, GroupViewSet, AssetWeightViewSet



# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups',GroupViewSet)
router.register(r'facts',AssetWeightViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path("api-auth/", include('rest_framework.urls', namespace='rest_framework')),
   
    path("weights/", AssetWeight.as_view(),name='total_asset_weights'),
    path("portfolio/", PortfolioValues.as_view(), name='portfolio_values'),

    path("portfolio_time_series/", views.portfolio_time_series, name='portfolio_values_graph'),
    path("asset_weights/", views.asset_weights, name='asset_weights_graph' ),
    path("portfolio_options", PortfolioOptions.as_view(), name='get_portfolio_names'),
    
]