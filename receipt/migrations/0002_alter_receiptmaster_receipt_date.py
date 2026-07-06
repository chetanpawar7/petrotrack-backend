import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("receipt", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receiptmaster",
            name="receipt_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
