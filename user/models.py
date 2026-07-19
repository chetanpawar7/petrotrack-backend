from django.db import models
from django.utils import timezone

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

    @property
    def current_subscription(self):
        return self.subscriptions.filter(status__in=['ACTIVE', 'TRIAL']).order_by('-end_date').first()


class SubscriptionPlanMaster(models.Model):
    BILLING_CYCLE_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('TRIAL', 'Trial'),
    )

    id = models.AutoField(primary_key=True)
    plan_name = models.CharField(max_length=100)
    plan_code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='MONTHLY')
    duration_days = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_users = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_subscription_plans')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_subscription_plans')

    class Meta:
        db_table = 'petrotrack_subscription_plan_master'
        ordering = ['price', 'id']

    def __str__(self):
        return self.plan_name


class FuelStationSubscription(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('TRIAL', 'Trial'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )

    id = models.AutoField(primary_key=True)
    fuel_station = models.ForeignKey(FuelStationMaster, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlanMaster, on_delete=models.PROTECT, related_name='station_subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=150, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_station_subscriptions')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_station_subscriptions')

    class Meta:
        db_table = 'petrotrack_fuel_station_subscription'
        ordering = ['-end_date', '-id']
        indexes = [
            models.Index(fields=['fuel_station', 'status']),
            models.Index(fields=['end_date']),
        ]

    @property
    def is_subscription_valid(self):
        return self.is_active and self.status in ['ACTIVE', 'TRIAL'] and self.end_date >= timezone.localdate()

    def __str__(self):
        return f'{self.fuel_station.station_name} - {self.plan.plan_name} - {self.status}'


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
    role = models.ForeignKey(RoleMaster, on_delete=models.CASCADE, related_name='sub_roles',blank=True, null=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL,blank=True, null=True, related_name='created_sub_roles')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_sub_roles')

    class Meta:
        db_table = 'petrotrack_sub_role_master'


class PageMaster(models.Model):
    id = models.AutoField(primary_key=True)
    page_name = models.CharField(max_length=100)
    page_code = models.CharField(max_length=100, unique=True)
    route_path = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='child_pages')
    display_order = models.PositiveIntegerField(default=0)
    is_menu = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_pages')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_pages')

    class Meta:
        db_table = 'petrotrack_page_master'
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.page_name


class PageDetail(models.Model):
    CONTROL_TYPE_CHOICES = (
        ('VIEW', 'View'),
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('EXPORT', 'Export'),
    )

    id = models.AutoField(primary_key=True)
    page = models.ForeignKey(PageMaster, on_delete=models.CASCADE, related_name='page_permissions')
    role = models.ForeignKey(RoleMaster, on_delete=models.CASCADE, related_name='page_permissions')
    sub_role = models.ForeignKey(SubRoleMaster, on_delete=models.CASCADE, blank=True, null=True, related_name='page_permissions')
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='created_page_permissions')
    updated_by = models.ForeignKey('user.UserMaster', on_delete=models.SET_NULL, blank=True, null=True, related_name='updated_page_permissions')

    class Meta:
        db_table = 'petrotrack_page_detail'
        unique_together = ('page', 'role', 'sub_role', 'control_type')

    def __str__(self):
        sub_role_name = self.sub_role.sub_role_name if self.sub_role else 'All'
        return f'{self.page.page_name} - {self.role.role_name} - {sub_role_name} - {self.control_type}'


class UserMaster(models.Model):
    id = models.AutoField(primary_key=True)
    supabase_user_id = models.UUIDField(unique=True,blank=True, null=True)
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

    @property
    def is_authenticated(self):
        return True

    @property
    def role_name(self):
        return self.role.role_name.upper() if self.role and self.role.role_name else None

    @property
    def is_admin(self):
        return self.role_name == "ADMIN"

    @property
    def is_manager(self):
        return self.role_name == "MANAGER"

    @property
    def is_operator(self):
        return self.role_name == "OPERATOR"

