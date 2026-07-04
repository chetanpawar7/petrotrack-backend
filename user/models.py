from django.db import models

# Create your models here.

class FuelStationMaster(models.Model):
    id = models.AutoField(primary_key=True)
    station_name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_stations')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_stations')

    class Meta:
        db_table = 'petrotrack_fuel_station_master'


class RoleMaster(models.Model):
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL,blank=True, null=True, related_name='created_roles')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_roles')

    class Meta:
        db_table = 'petrotrack_role_master'

class SubRoleMaster(models.Model):
    id = models.AutoField(primary_key=True)
    sub_role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL,blank=True, null=True, related_name='created_sub_roles')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_sub_roles')

    class Meta:
        db_table = 'petrotrack_sub_role_master'


class UserMaster(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.TextField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, unique=True)
    role = models.ForeignKey(RoleMaster, on_delete=models.SET_NULL, blank=True, null=True)
    sub_role = models.ForeignKey(SubRoleMaster, on_delete=models.SET_NULL, blank=True, null=True)
    fuel_station = models.ForeignKey(FuelStationMaster, on_delete=models.SET_NULL, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_users')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_users')

    class Meta:
        db_table = 'petrotrack_user_master'

