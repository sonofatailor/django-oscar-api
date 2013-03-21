from django.test import TestCase
from django.utils import simplejson as json

from oscar_testsupport.factories import create_product


class TestProductAPI(TestCase):
    """
    Product API
    """

    def setUp(self):
        self.product = create_product()

    def test_get_list(self):
        response = self.client.get('/api/products/')
        self.assertEqual(200, response.status_code)
        products = json.loads(response.content)
        self.assertEqual(1, len(products))
        product = products[0]
        for key in ('title', 'description'):
            self.assertTrue(key in product)

    def test_get_detail(self):
        response = self.client.get('/api/products/%d/' % self.product.pk)
        self.assertEqual(200, response.status_code)
        product = json.loads(response.content)
        for key in ('title', 'description'):
            self.assertTrue(key in product)
