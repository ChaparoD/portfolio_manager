from django.urls import path, include
from assets import views
from .views import AssetWeight, PortfolioValues
from rest_framework import routers
from .views import UserViewSet, GroupViewSet, AssetWeightViewSet



# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups',GroupViewSet)
router.register(r'facts',AssetWeightViewSet)


urlpatterns = [
    path("", views.home, name="home"),
    path('', include(router.urls)),
    path("weights/", AssetWeight.as_view(),name='asset_weights'),
    path("portfolio/", PortfolioValues.as_view(), name='portfolio_values'),
    path("api-auth/", include('rest_framework.urls', namespace='rest_framework')),
]