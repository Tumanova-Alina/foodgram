import base64

import webcolors
from django.core.files.base import ContentFile
from rest_framework import serializers

from .constants import COLOR_HAVE_NO_NAME


class Hex2NameColor(serializers.Field):

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(COLOR_HAVE_NO_NAME)
        return data


class Base64ImageField(serializers.ImageField):
    """Кодирование изображения."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f'temp.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

        return super().to_internal_value(data)
