from oscar.apps.catalogue import models

from rest_framework import serializers


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Product
        fields = ('title', 'description', 'product_class')

