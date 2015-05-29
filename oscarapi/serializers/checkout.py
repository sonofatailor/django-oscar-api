import warnings

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.translation import gettext as _
from oscar.core import prices
from oscar.core.loading import get_class, get_model
from rest_framework import serializers, exceptions

from oscarapi.basket.operations import (
    assign_basket_strategy,
    get_total_price
)
from oscarapi.serializers import (
    VoucherSerializer,
    OfferDiscountSerializer
)
from oscarapi.utils import (
    OscarHyperlinkedModelSerializer,
    OscarModelSerializer,
    overridable
)

OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
ShippingAddress = get_model('order', 'ShippingAddress')
BillingAddress = get_model('order', 'BillingAddress')
Order = get_model('order', 'Order')
OrderLine = get_model('order', 'Line')
OrderLineAttribute = get_model('order', 'LineAttribute')

Basket = get_model('basket', 'Basket')
Country = get_model('address', 'Country')
Repository = get_class('shipping.repository', 'Repository')


class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(
        max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY, required=False)
    excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=True)
    incl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)
    tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)


class CountrySerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = Country


class ShippingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = ShippingAddress


class InlineShippingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(
        view_name='country-detail', queryset=Country.objects)

    class Meta:
        model = ShippingAddress


class BillingAddressSerializer(OscarHyperlinkedModelSerializer):
    class Meta:
        model = BillingAddress


class InlineBillingAddressSerializer(OscarModelSerializer):
    country = serializers.HyperlinkedRelatedField(
        view_name='country-detail', queryset=Country.objects)

    class Meta:
        model = BillingAddress


class ShippingMethodSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=128)
    price = serializers.SerializerMethodField('calculate_price')

    def calculate_price(self, obj):
        price = obj.calculate(self.context.get('basket'))
        return PriceSerializer(price).data


class OrderLineAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='order-lineattributes-detail')

    class Meta:
        model = OrderLineAttribute


class OrderLineSerializer(OscarHyperlinkedModelSerializer):
    "This serializer renames some fields so they match up with the basket"

    url = serializers.HyperlinkedIdentityField(view_name='order-lines-detail')
    attributes = OrderLineAttributeSerializer(
        many=True, fields=('url', 'option', 'value'), required=False)
    price_currency = serializers.DecimalField(decimal_places=2, max_digits=12,
                                              source='order.currency')
    price_excl_tax = serializers.DecimalField(decimal_places=2, max_digits=12,
                                              source='line_price_excl_tax')
    price_incl_tax = serializers.DecimalField(decimal_places=2, max_digits=12,
                                              source='line_price_incl_tax')
    price_incl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12,
        source='line_price_before_discounts_incl_tax')
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12,
        source='line_price_before_discounts_excl_tax')

    class Meta:
        model = OrderLine
        fields = overridable('OSCAR_ORDERLINE_FIELD', default=[
            'attributes', 'url', 'product', 'stockrecord', 'quantity',
            'price_currency', 'price_excl_tax', 'price_incl_tax',
            'price_incl_tax_excl_discounts', 'price_excl_tax_excl_discounts',
            'order'
        ])


class OrderOfferDiscountSerializer(OfferDiscountSerializer):
    name = serializers.CharField(source='offer_name')
    amount = serializers.DecimalField(decimal_places=2, max_digits=12)


class OrderVoucherOfferSerializer(OrderOfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)


class OrderSerializer(OscarHyperlinkedModelSerializer):
    """
    The order serializer tries to have the same kind of structure as the
    basket. That way the same kind of logic can be used to display the order
    as the basket in the checkout process.
    """
    owner = serializers.HyperlinkedRelatedField(view_name='user-detail',
                                                source='user', read_only=True)
    lines = serializers.HyperlinkedIdentityField(view_name='order-lines-list')
    shipping_address = InlineShippingAddressSerializer(
        many=False, required=False)
    billing_address = InlineBillingAddressSerializer(
        many=False, required=False)

    payment_url = serializers.SerializerMethodField('get_payment_url')
    offer_discounts = serializers.SerializerMethodField('get_offer_discounts')
    voucher_discounts = serializers.SerializerMethodField('get_voucher_discounts')

    def get_offer_discounts(self, obj):
        qs = obj.basket_discounts.filter(offer_id__isnull=False)
        return OrderOfferDiscountSerializer(qs, many=True).data

    def get_voucher_discounts(self, obj):
        qs = obj.basket_discounts.filter(voucher_id__isnull=False)
        return OrderVoucherOfferSerializer(qs, many=True).data

    def get_payment_url(self, obj):
        try:
            return reverse('api-payment', args=(obj.pk,))
        except NoReverseMatch:
            msg = "You need to implement a view named 'api-payment' " \
                "which redirects to the payment provider and sets up the " \
                "callbacks."
            warnings.warn(msg)
            return msg

    class Meta:
        model = Order
        fields = overridable('OSCARAPI_ORDER_FIELD', default=(
            'number', 'basket', 'url',
            'user', 'billing_address', 'currency', 'total_incl_tax',
            'total_excl_tax', 'shipping_incl_tax', 'shipping_excl_tax',
            'shipping_address', 'shipping_method', 'shipping_code', 'status',
            'guest_email', 'date_placed', 'payment_url', 'offer_discounts',
            'voucher_discounts'))


class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail', queryset=Basket.objects)
    total = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False)
    shipping_method_code = serializers.CharField(
        max_length=128, required=False)
    shipping_charge = PriceSerializer(many=False, required=False)
    shipping_address = ShippingAddressSerializer(many=False, required=False)
    billing_address = BillingAddressSerializer(many=False, required=False)

    def get_initial_order_status(self, basket):
        return overridable('OSCARAPI_INITIAL_ORDER_STATUS', default='new')

    def validate(self, attrs):
        request = self.context['request']

        if request.user.is_anonymous() and not settings.OSCAR_ALLOW_ANON_CHECKOUT:
            message = _('Anonymous checkout forbidden')
            raise serializers.ValidationError(message)

        basket = attrs.get('basket')
        basket = assign_basket_strategy(basket, request)
        shipping_method = self._shipping_method(
            request, basket,
            attrs.get('shipping_method_code'),
            attrs.get('shipping_address')
        )
        shipping_charge = shipping_method.calculate(basket)
        posted_shipping_charge = attrs.get('shipping_charge')

        if posted_shipping_charge is not None:
            posted_shipping_charge = prices.Price(**posted_shipping_charge)
            # test submitted data.
            if not posted_shipping_charge == shipping_charge:
                message = _('Shipping price incorrect %s != %s' % (
                    posted_shipping_charge, shipping_charge
                ))
                raise serializers.ValidationError(message)

        total = attrs.get('total')
        if total is not None:
            if total != basket.total_incl_tax:
                message = _('Total incorrect %s != %s' % (
                    total,
                    basket.total_incl_tax
                ))
                raise serializers.ValidationError(message)

        # update attrs with validated data.
        attrs['total'] = get_total_price(basket)
        attrs['shipping_method'] = shipping_method
        attrs['shipping_charge'] = shipping_charge
        attrs['basket'] = basket
        return attrs

    def create(self, validated_data):
        try:
            basket = validated_data.get('basket')
            order_number = self.generate_order_number(basket)
            request = self.context['request']
            shipping_address = ShippingAddress(
                **validated_data['shipping_address'])
            return self.place_order(
                order_number=order_number,
                user=request.user,
                basket=basket,
                shipping_address=shipping_address,
                shipping_method=validated_data.get('shipping_method'),
                shipping_charge=validated_data.get('shipping_charge'),
                billing_address=validated_data.get('billing_address'),
                order_total=validated_data.get('total'),
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)

    def _shipping_method(self, request, basket,
                         shipping_method_code, shipping_address):
        repo = Repository()

        default = repo.get_default_shipping_method(
            basket=basket,
            user=request.user,
            request=request,
            shipping_addr=shipping_address
        )

        if shipping_method_code is not None:
            methods = repo.get_shipping_methods(
                basket=basket,
                user=request.user,
                request=request,
                shipping_addr=shipping_address
            )

            find_method = (
                s for s in methods if s.code == shipping_method_code)
            shipping_method = next(find_method, default)
            return shipping_method

        return default
