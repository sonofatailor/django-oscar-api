from django.conf.urls.defaults import patterns, include

from . import api

product_resource = api.ProductResource()


urlpatterns = patterns('',
    (r'', include(product_resource.urls)),
)
