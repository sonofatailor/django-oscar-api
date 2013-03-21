from django.conf.urls.defaults import *
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = patterns('',
    url(r'^$', views.api_root),
    url(r'^product-classes/$', views.ProductClassList.as_view(),
        name='productclass-list'),
    url(r'^product-classes/(?P<pk>\d+)/$', views.ProductClassDetail.as_view(),
        name='productclass-detail'),
    url(r'^products/$', views.ProductList.as_view(), name='product-list'),
    url(r'^products/(?P<pk>\d+)/$', views.ProductDetail.as_view(),
        name='product-detail'),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
)

urlpatterns = format_suffix_patterns(
    urlpatterns, allowed=['json', 'api'])
