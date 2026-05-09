# plataforma_config/serializers.py
from rest_framework import serializers
from .models import PlatformSetting


class PlatformSettingPublicSerializer(serializers.ModelSerializer):
    """
    Serializer público — solo datos que el frontend necesita.
    Sin datos sensibles de soporte.
    """
    soporte_whatsapp_url = serializers.SerializerMethodField()

    class Meta:
        model = PlatformSetting
        fields = [
            'platform_name',
            'platform_description',
            'platform_logo',
            'favicon',
            'primary_color_hex',
            'secondary_color_hex',
            'store_card_layout',
            'terms_and_conditions',
            'privacy_policy',
            'soporte_whatsapp_url',
            'last_updated',
        ]
        read_only_fields = fields

    def get_soporte_whatsapp_url(self, obj):
        if obj.soporte_whatsapp:
            numero = obj.soporte_whatsapp.replace('+', '')
            return f"https://wa.me/{numero}"
        return None


class PlatformSettingAdminSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el admin — incluye todos los campos.
    """
    soporte_whatsapp_url = serializers.SerializerMethodField()

    class Meta:
        model = PlatformSetting
        fields = [
            'id',
            'platform_name',
            'platform_description',
            'platform_logo',
            'favicon',
            'primary_color_hex',
            'secondary_color_hex',
            'store_card_layout',
            'terms_and_conditions',
            'privacy_policy',
            'soporte_email',
            'soporte_whatsapp',
            'soporte_whatsapp_url',
            'last_updated',
        ]
        read_only_fields = ['id', 'last_updated', 'soporte_whatsapp_url']

    def get_soporte_whatsapp_url(self, obj):
        if obj.soporte_whatsapp:
            numero = obj.soporte_whatsapp.replace('+', '')
            return f"https://wa.me/{numero}"
        return None

    def validate_primary_color_hex(self, value):
        import re
        if value and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
            raise serializers.ValidationError(
                f"Color HEX inválido. Usa formato #RRGGBB. Ej: #FF5733"
            )
        return value

    def validate_secondary_color_hex(self, value):
        import re
        if value and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
            raise serializers.ValidationError(
                f"Color HEX inválido. Usa formato #RRGGBB. Ej: #33C1FF"
            )
        return value