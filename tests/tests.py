from django.test import TestCase
from tastypie.test import ResourceTestCase
from oscar_testsupport.factories import create_product
from oscar.apps.catalogue.models import Category


class TestProductResource(ResourceTestCase):

    def setUp(self):
        super(TestProductResource, self).setUp()
        self.product = create_product()

    def test_get_list(self):
        response = self.api_client.get('/api/v1/products/', format='json')
        self.assertHttpOK(response)

        data = self.deserialize(response)
        self.assertEqual(1, data['meta']['total_count'])
        product_payload = data['objects'][0]
        required_keys = ('title', 'image_url')
        for key in required_keys:
            self.assertTrue(key in product_payload)

    def test_get_detail(self):
        response = self.api_client.get('/api/v1/products/%d/' % self.product.pk, format='json')
        self.assertHttpOK(response)

        payload = self.deserialize(response)
        required_keys = ('title', 'image_url')
        for key in required_keys:
            self.assertTrue(key in payload)


class TestCategoryResource(ResourceTestCase):

    def setUp(self):
        super(TestCategoryResource, self).setUp()
        self.category = Category.add_root(name="Fiction")

    def test_get_list(self):
        response = self.api_client.get('/api/v1/categories/', format='json')
        self.assertHttpOK(response)

    def test_get_detail(self):
        response = self.api_client.get(
            '/api/v1/categories/%d/' % self.category.pk, format='json')
        self.assertHttpOK(response)