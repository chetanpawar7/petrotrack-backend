import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_pagemaster_pagedetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlanMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('plan_name', models.CharField(max_length=100)),
                ('plan_code', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('billing_cycle', models.CharField(choices=[('MONTHLY', 'Monthly'), ('QUARTERLY', 'Quarterly'), ('YEARLY', 'Yearly'), ('TRIAL', 'Trial')], default='MONTHLY', max_length=20)),
                ('duration_days', models.PositiveIntegerField(default=30)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('max_users', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_subscription_plans', to='user.usermaster')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_subscription_plans', to='user.usermaster')),
            ],
            options={
                'db_table': 'petrotrack_subscription_plan_master',
                'ordering': ['price', 'id'],
            },
        ),
        migrations.CreateModel(
            name='FuelStationSubscription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('TRIAL', 'Trial'), ('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('start_date', models.DateField(default=django.utils.timezone.localdate)),
                ('end_date', models.DateField()),
                ('payment_status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded')], default='PENDING', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('payment_reference', models.CharField(blank=True, max_length=150, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_station_subscriptions', to='user.usermaster')),
                ('fuel_station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='user.fuelstationmaster')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='station_subscriptions', to='user.subscriptionplanmaster')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_station_subscriptions', to='user.usermaster')),
            ],
            options={
                'db_table': 'petrotrack_fuel_station_subscription',
                'ordering': ['-end_date', '-id'],
                'indexes': [
                    models.Index(fields=['fuel_station', 'status'], name='petrotrack__fuel_s_32d78b_idx'),
                    models.Index(fields=['end_date'], name='petrotrack__end_dat_1d6b80_idx'),
                ],
            },
        ),
    ]
