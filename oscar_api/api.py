from tastypie.resources import ModelResource
from tastypie.constants import ALL

from oscar.apps.catalogue import models


class ProductResource(ModelResource):
    class Meta:
        queryset = models.Product.browsable.all()
        resource_name = 'products'
        excludes = ('date_created', 'date_updated', 'status', 'slug')
        filtering = {
            'title': ALL,
        }

    def dehydrate(self, bundle):
        # Add extra fields to the serialised object
        product = bundle.obj
        bundle.data['site_url'] = product.get_absolute_url()
        image = product.primary_image()
        if hasattr(image, 'keys'):
            bundle.data['image_url'] = image['original'].name
        else:
            bundle.data['image_url'] = product.primary_image().original.url
        return bundle
