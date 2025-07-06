# plataforma_config/serializers.py
from rest_framework import serializers
from .models import PlatformSetting

class PlatformSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSetting
        fields = [
            'id', 'platform_logo', 'primary_color_hex', 'secondary_color_hex',
            'terms_and_conditions', 'privacy_policy', 'store_card_layout', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']