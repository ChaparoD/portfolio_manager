from rest_framework import serializers, viewsets
from .models import Asset, Portfolio, FactsDailyPrices
from django.contrib.auth.models import Group, User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class PortfolioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Portfolio
        fields = ['name', 'initial_value']


class AssetSerializer(serializers.ModelSerializer):
    portfolio = PortfolioSerializer()

    class Meta:
        model = Asset
        fields = ['name', 'initial_weight', 'quantity', 'portfolio']


class AssetWeightSerializer(serializers.HyperlinkedModelSerializer):
    asset = AssetSerializer()

    class Meta:
        model = FactsDailyPrices
        fields = ['date', 'asset', 'price', 'asset_value']
        




