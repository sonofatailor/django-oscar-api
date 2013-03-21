from rest_framework.decorators import api_view
from rest_framework import generics, response, reverse

from oscar.apps.catalogue import models

from . import serializers


@api_view(['GET'])
def api_root(request, format=None):
    return response.Response({
        'products': reverse.reverse('product-list', request=request)
    })


class ProductList(generics.ListAPIView):
    model = models.Product
    serializer_class = serializers.ProductSerializer


class ProductDetail(generics.RetrieveAPIView):
    model = models.Product
    serializer_class = serializers.ProductSerializer


class ProductClassList(generics.ListAPIView):
    model = models.ProductClass


class ProductClassDetail(generics.RetrieveAPIView):
    model = models.ProductClass
