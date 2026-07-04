from rest_framework import serializers
from user.models import UserMaster, RoleMaster, SubRoleMaster

class UserListSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    sub_role_name = serializers.SerializerMethodField()
    station_name = serializers.SerializerMethodField()

    class Meta:
        model = UserMaster
        fields = ['id', 'username','first_name', 'last_name', 'email','mobile_number', 'role_name', 'sub_role_name', 'station_name','is_active', 'updated_at', 'updated_at']

    def get_role_name(self, obj):
        return obj.role.role_name if obj.role else None

    def get_sub_role_name(self, obj):
        return obj.sub_role.sub_role_name if obj.sub_role else None
    
    def get_station_name(self, obj):
        return obj.fuel_station.station_name if obj.fuel_station else None


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaster
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'mobile_number', 'role', 'sub_role', 'fuel_station', 'is_active']