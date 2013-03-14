from django.conf.urls.defaults import patterns, include
from tastypie.api import Api

from . import api

v1_api = Api(api_name='v1')
v1_api.register(api.ProductResource())
v1_api.register(api.CategoryResource())

urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
