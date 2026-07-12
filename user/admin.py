from django.contrib import admin

from user.models import (
    FuelStationMaster,
    FuelStationSubscription,
    PageDetail,
    PageMaster,
    RoleMaster,
    SubRoleMaster,
    SubscriptionPlanMaster,
    UserMaster,
)


@admin.register(FuelStationMaster)
class FuelStationMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'station_name', 'pincode', 'is_active')
    search_fields = ('station_name', 'pincode')
    list_filter = ('is_active',)


@admin.register(SubscriptionPlanMaster)
class SubscriptionPlanMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan_name', 'plan_code', 'billing_cycle', 'duration_days', 'price', 'max_users', 'is_active')
    search_fields = ('plan_name', 'plan_code')
    list_filter = ('billing_cycle', 'is_active')


@admin.register(FuelStationSubscription)
class FuelStationSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fuel_station',
        'plan',
        'status',
        'start_date',
        'end_date',
        'payment_status',
        'amount',
        'is_active',
    )
    search_fields = ('fuel_station__station_name', 'plan__plan_name', 'plan__plan_code', 'payment_reference')
    list_filter = ('status', 'payment_status', 'plan', 'is_active')
    date_hierarchy = 'end_date'


@admin.register(RoleMaster)
class RoleMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name', 'is_active')
    search_fields = ('role_name',)
    list_filter = ('is_active',)


@admin.register(SubRoleMaster)
class SubRoleMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'sub_role_name', 'role', 'is_active')
    search_fields = ('sub_role_name', 'role__role_name')
    list_filter = ('is_active', 'role')


@admin.register(UserMaster)
class UserMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'sub_role', 'fuel_station', 'is_active')
    search_fields = ('username', 'email', 'mobile_number')
    list_filter = ('is_active', 'role', 'sub_role', 'fuel_station')


@admin.register(PageMaster)
class PageMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'page_name', 'page_code', 'route_path', 'source', 'parent', 'display_order', 'is_menu', 'is_active')
    search_fields = ('page_name', 'page_code', 'route_path', 'source')
    list_filter = ('source', 'is_menu', 'is_active', 'parent')
    ordering = ('display_order', 'id')


@admin.register(PageDetail)
class PageDetailAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'page',
        'role',
        'sub_role',
        'control_type',
        'is_active',
    )
    search_fields = ('page__page_name', 'page__page_code', 'role__role_name', 'sub_role__sub_role_name')
    list_filter = ('is_active', 'role', 'sub_role', 'control_type')
