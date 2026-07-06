from django.db import models

from django.db import models, transaction
from decimal import Decimal
from django.utils import timezone


class ReceiptMaster(models.Model):
    SHIFT_CHOICES = (
        ("MORNING", "Morning"),
        ("EVENING", "Evening"),
        ("NIGHT", "Night"),
    )

    STATUS_CHOICES = (
        ("BALANCED", "Balanced"),
        ("SHORT", "Cash Short"),
        ("EXCESS", "Cash Excess"),
    )

    id = models.AutoField(primary_key=True)

    receipt_no = models.CharField(
        max_length=50,
        unique=True,
        blank=True
    )

    receipt_date = models.DateField(default=timezone.localdate)
    shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES,
        blank=True
    )

    operator = models.ForeignKey(
        "user.UserMaster",
        on_delete=models.PROTECT,
        related_name="receipts",
    )

    total_fuel_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_collection = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="BALANCED"
    )

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        "user.UserMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_receipts",
    )

    updated_by = models.ForeignKey(
        "user.UserMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_receipts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "petrotrack_receipt_master"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            with transaction.atomic():
                last_receipt = (
                    ReceiptMaster.objects
                    .select_for_update()
                    .order_by("-id")
                    .first()
                )

                if last_receipt and last_receipt.receipt_no:
                    last_no = int(last_receipt.receipt_no.split("-")[-1])
                    self.receipt_no = f"RCPT-{last_no + 1:05d}"
                else:
                    self.receipt_no = "RCPT-00001"

        self.difference = self.actual_cash - self.expected_cash

        if self.difference == Decimal("0.00"):
            self.status = "BALANCED"
        elif self.difference < Decimal("0.00"):
            self.status = "SHORT"
        else:
            self.status = "EXCESS"

        if not self.shift:
            current_hour = timezone.localtime().hour

            if current_hour < 12:
                self.shift = "MORNING"
            elif current_hour < 18:
                self.shift = "EVENING"
            else:
                self.shift = "NIGHT"


        super().save(*args, **kwargs) 


class ReceiptFuelSale(models.Model):
    FUEL_TYPE_CHOICES = (
        ("PETROL", "Petrol"),
        ("DIESEL", "Diesel"),
    )

    id = models.AutoField(primary_key=True)

    receipt = models.ForeignKey(
        ReceiptMaster,
        on_delete=models.CASCADE,
        related_name="fuel_sales",
    )

    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)

    opening_reading = models.DecimalField(max_digits=12, decimal_places=2)
    closing_reading = models.DecimalField(max_digits=12, decimal_places=2)
    testing_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_per_liter = models.DecimalField(max_digits=12, decimal_places=2)

    total_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "petrotrack_receipt_fuel_sale"
        unique_together = ("receipt", "fuel_type")



class ReceiptCollection(models.Model):
    id = models.AutoField(primary_key=True)

    receipt = models.OneToOneField(
        ReceiptMaster,
        on_delete=models.CASCADE,
        related_name="collection",
    )

    cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_collection = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "petrotrack_receipt_collection"


class ReceiptExpense(models.Model):
    id = models.AutoField(primary_key=True)

    receipt = models.ForeignKey(
        ReceiptMaster,
        on_delete=models.CASCADE,
        related_name="expenses",
    )

    expense_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "petrotrack_receipt_expense"


class ReceiptDenomination(models.Model):
    id = models.AutoField(primary_key=True)

    receipt = models.OneToOneField(
        ReceiptMaster,
        on_delete=models.CASCADE,
        related_name="denomination",
    )

    note_500 = models.PositiveIntegerField(default=0)
    note_200 = models.PositiveIntegerField(default=0)
    note_100 = models.PositiveIntegerField(default=0)
    note_50 = models.PositiveIntegerField(default=0)
    note_20 = models.PositiveIntegerField(default=0)
    note_10 = models.PositiveIntegerField(default=0)
    coins = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "petrotrack_receipt_denomination"
