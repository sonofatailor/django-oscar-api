from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

from oscarapi.utils import overridable


User = get_user_model()


def field_length(fieldname):
    field = next(
        field for field in User._meta.fields if field.name == fieldname)
    return field.max_length


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = overridable('OSCARAPI_USER_FIELDS', (
            'email', 'id', 'date_joined',))


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(
        max_length=field_length('email'), required=True)
    password = serializers.CharField(
        max_length=field_length('password'), required=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['email'],
                            password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('invalid login')
        elif not user.is_active:
            raise serializers.ValidationError(
                'Can not log in as inactive user')
        elif user.is_staff and overridable(
                'OSCARAPI_BLOCK_ADMIN_API_ACCESS', True):
            raise serializers.ValidationError(
                'Staff users can not log in via the rest api')

        self.object = user
        return attrs
