import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_subrolemaster_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('page_name', models.CharField(max_length=100)),
                ('page_code', models.CharField(max_length=100, unique=True)),
                ('route_path', models.CharField(max_length=255, unique=True)),
                ('icon', models.CharField(blank=True, max_length=100, null=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_menu', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_pages', to='user.usermaster')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_pages', to='user.pagemaster')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_pages', to='user.usermaster')),
            ],
            options={
                'db_table': 'petrotrack_page_master',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PageDetail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('control_type', models.CharField(choices=[('VIEW', 'View'), ('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete'), ('EXPORT', 'Export')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_page_permissions', to='user.usermaster')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='page_permissions', to='user.pagemaster')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='page_permissions', to='user.rolemaster')),
                ('sub_role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='page_permissions', to='user.subrolemaster')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_page_permissions', to='user.usermaster')),
            ],
            options={
                'db_table': 'petrotrack_page_detail',
                'unique_together': {('page', 'role', 'sub_role', 'control_type')},
            },
        ),
    ]
