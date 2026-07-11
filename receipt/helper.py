from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response

from receipt.models import (
    ReceiptMaster,
    ReceiptCollection,
    ReceiptExpense,
    ReceiptDenomination,
    ReceiptFuelSale,
)
from user.models import UserMaster
from utils import error_msg, response_translator, success_msg


DECIMAL_ZERO = Decimal("0.00")


def _to_decimal(value, field_name, errors, required=True):
    if value in (None, ""):
        if required:
            errors.append(f"{field_name} is required")
        return DECIMAL_ZERO

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        errors.append(f"{field_name} must be a valid number")
        return DECIMAL_ZERO

    if decimal_value < DECIMAL_ZERO:
        errors.append(f"{field_name} cannot be negative")

    return decimal_value


def _to_int(value, field_name, errors):
    if value in (None, ""):
        return 0

    try:
        int_value = int(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be a valid integer")
        return 0

    if int_value < 0:
        errors.append(f"{field_name} cannot be negative")

    return int_value


def _decimal_to_string(value):
    return str(Decimal(value).quantize(Decimal("0.01")))


def _summary_data(receipts):
    summary = receipts.aggregate(
        total_receipts=Count("id"),
        total_fuel_sales=Sum("total_fuel_sales"),
        balanced=Count("id", filter=Q(status="BALANCED")),
        short=Count("id", filter=Q(status="SHORT")),
        excess=Count("id", filter=Q(status="EXCESS")),
    )
    short_count = summary.get("short") or 0
    excess_count = summary.get("excess") or 0

    return {
        "total_receipts": summary.get("total_receipts") or 0,
        "total_fuel_sales": _decimal_to_string(summary.get("total_fuel_sales") or DECIMAL_ZERO),
        "balanced": summary.get("balanced") or 0,
        "mismatch": short_count + excess_count,
        "short": short_count,
        "excess": excess_count,
    }


def _filter_receipts_for_user(receipts, user):
    if not isinstance(user, UserMaster):
        return receipts.none()

    if user.is_admin:
        return receipts

    if user.is_manager:
        return receipts.filter(operator__fuel_station_id=user.fuel_station_id)

    return receipts.filter(operator=user)


def _can_manage_operator(user, operator):
    if not isinstance(user, UserMaster) or not operator:
        return False

    if user.is_admin:
        return True

    if user.is_manager:
        return operator.is_operator and operator.fuel_station_id == user.fuel_station_id

    return user.id == operator.id


def get_dashboard(request):
    try:
        selected_date_value = request.data.get("selected_date")
        selected_date = parse_date(selected_date_value) if selected_date_value else timezone.localdate()
        if not selected_date:
            response = response_translator.error_response(
                message=error_msg.INVALID_SELECTED_DATE
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        receipts = ReceiptMaster.objects.filter(
            receipt_date=selected_date,
            is_active=True,
            is_deleted=False,
        )
        receipts = _filter_receipts_for_user(receipts, request.user)

        totals = receipts.aggregate(
            total_fuel_sales=Sum("total_fuel_sales"),
            total_collection=Sum("total_collection"),
            total_expenses=Sum("total_expenses"),
            expected_balance=Sum("expected_cash"),
            actual_cash=Sum("actual_cash"),
            receipts_generated=Count("id"),
        )

        expected_balance = totals.get("expected_balance") or DECIMAL_ZERO
        actual_cash = totals.get("actual_cash") or DECIMAL_ZERO
        difference = actual_cash - expected_balance
        if difference == DECIMAL_ZERO:
            closing_status = "BALANCED"
        elif difference < DECIMAL_ZERO:
            closing_status = "SHORT"
        else:
            closing_status = "EXCESS"

        data = {
            "selected_date": str(selected_date),
            "today_fuel_sales": _decimal_to_string(
                totals.get("total_fuel_sales") or DECIMAL_ZERO
            ),
            "total_collection": _decimal_to_string(
                totals.get("total_collection") or DECIMAL_ZERO
            ),
            "total_expenses": _decimal_to_string(
                totals.get("total_expenses") or DECIMAL_ZERO
            ),
            "receipts_generated": totals.get("receipts_generated") or 0,
            "closing_status": {
                "expected_balance": _decimal_to_string(expected_balance),
                "actual_cash": _decimal_to_string(actual_cash),
                "difference": _decimal_to_string(difference),
                "status": closing_status,
            },
        }
        response = response_translator.success_response(
            data=data,
            message=success_msg.DASHBOARD_DATA_FETCHED,
        )
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        raise e


def _get_operator(request, request_data):
    request_user = getattr(request, "user", None)
    operator_id = request_data.get("operator_id")

    if operator_id:
        operator = UserMaster.objects.filter(id=operator_id, is_active=True).first()
        if not _can_manage_operator(request_user, operator):
            return None
        return operator

    if isinstance(request_user, UserMaster) and request_user.is_operator:
        return request_user

    return None


def _receipt_data(receipt):
    fuel_sales = [
        {
            "fuel_type": fuel_sale.fuel_type,
            "opening_reading": _decimal_to_string(fuel_sale.opening_reading),
            "closing_reading": _decimal_to_string(fuel_sale.closing_reading),
            "testing_qty": _decimal_to_string(fuel_sale.testing_qty),
            "rate_per_liter": _decimal_to_string(fuel_sale.rate_per_liter),
            "total_qty": _decimal_to_string(fuel_sale.total_qty),
            "sale_qty": _decimal_to_string(fuel_sale.sale_qty),
            "amount": _decimal_to_string(fuel_sale.amount),
        }
        for fuel_sale in receipt.fuel_sales.all()
    ]

    expenses = [
        {
            "expense_name": expense.expense_name,
            "amount": _decimal_to_string(expense.amount),
        }
        for expense in receipt.expenses.all()
    ]

    collection = getattr(receipt, "collection", None)
    denomination = getattr(receipt, "denomination", None)

    return {
        "receipt_id": receipt.id,
        "receipt_no": receipt.receipt_no,
        "receipt_date": receipt.receipt_date.isoformat(),
        "shift": receipt.shift,
        "operator_id": receipt.operator_id,
        "total_fuel_sales": _decimal_to_string(receipt.total_fuel_sales),
        "total_collection": _decimal_to_string(receipt.total_collection),
        "total_expenses": _decimal_to_string(receipt.total_expenses),
        "expected_cash": _decimal_to_string(receipt.expected_cash),
        "actual_cash": _decimal_to_string(receipt.actual_cash),
        "difference": _decimal_to_string(receipt.difference),
        "status": receipt.status,
        "fuel_sales": fuel_sales,
        "collection": {
            "cash": _decimal_to_string(collection.cash),
            "qr": _decimal_to_string(collection.qr),
            "card": _decimal_to_string(collection.card),
            "credit": _decimal_to_string(collection.credit),
            "total_collection": _decimal_to_string(collection.total_collection),
        } if collection else None,
        "expenses": expenses,
        "denomination": {
            "note_500": denomination.note_500,
            "note_200": denomination.note_200,
            "note_100": denomination.note_100,
            "note_50": denomination.note_50,
            "note_20": denomination.note_20,
            "note_10": denomination.note_10,
            "coins": _decimal_to_string(denomination.coins),
            "total_cash": _decimal_to_string(denomination.total_cash),
        } if denomination else None,
    }


def _receipt_list_data(receipt):
    operator_name = " ".join(
        part for part in [receipt.operator.first_name, receipt.operator.last_name] if part
    ).strip()

    return {
        "receipt_no": receipt.receipt_no,
        "date": receipt.receipt_date.isoformat(),
        "shift": receipt.shift,
        "operator_id": receipt.operator_id,
        "operator": operator_name or receipt.operator.username,
        "fuel_sales": _decimal_to_string(receipt.total_fuel_sales),
        "collection": _decimal_to_string(receipt.total_collection),
        "expenses": _decimal_to_string(receipt.total_expenses),
        "difference": _decimal_to_string(receipt.difference),
        "status": receipt.status,
    }


def _receipt_detail_data(receipt):
    data = _receipt_data(receipt)
    operator_name = " ".join(
        part for part in [receipt.operator.first_name, receipt.operator.last_name] if part
    ).strip()
    data["operator_name"] = operator_name or receipt.operator.username
    data["station_name"] = (
        receipt.operator.fuel_station.station_name
        if receipt.operator.fuel_station else None
    )
    return data


def create_receipt(request):
    try:
        request_data = request.data
        errors = []

        receipt_date = request_data.get("receipt_date")
        shift = request_data.get("shift")
        fuel_sales_data = request_data.get("fuel_sales")
        collection_data = request_data.get("collection")
        expenses_data = request_data.get("expenses", [])
        denomination_data = request_data.get("denomination")

        if not receipt_date:
            errors.append("receipt_date is required")

        valid_shifts = {choice[0] for choice in ReceiptMaster.SHIFT_CHOICES}
        if shift not in valid_shifts:
            errors.append("shift must be MORNING, EVENING, or NIGHT")

        if not isinstance(fuel_sales_data, list) or not fuel_sales_data:
            errors.append("fuel_sales must contain at least one item")

        if not isinstance(collection_data, dict):
            errors.append("collection is required")
            collection_data = {}

        if not isinstance(expenses_data, list):
            errors.append("expenses must be a list")
            expenses_data = []

        if not isinstance(denomination_data, dict):
            errors.append("denomination is required")
            denomination_data = {}

        operator = _get_operator(request, request_data)
        if not operator:
            errors.append("operator not found or permission denied")

        valid_fuel_types = {choice[0] for choice in ReceiptFuelSale.FUEL_TYPE_CHOICES}
        seen_fuel_types = set()
        fuel_sales = []
        total_fuel_sales = DECIMAL_ZERO

        if isinstance(fuel_sales_data, list):
            for index, fuel_sale_data in enumerate(fuel_sales_data):
                prefix = f"fuel_sales[{index}]"
                if not isinstance(fuel_sale_data, dict):
                    errors.append(f"{prefix} must be an object")
                    continue

                fuel_type = fuel_sale_data.get("fuel_type")
                if fuel_type not in valid_fuel_types:
                    errors.append(f"{prefix}.fuel_type must be PETROL or DIESEL")
                elif fuel_type in seen_fuel_types:
                    errors.append(f"{prefix}.fuel_type is duplicated")
                seen_fuel_types.add(fuel_type)

                opening_reading = _to_decimal(fuel_sale_data.get("opening_reading"), f"{prefix}.opening_reading", errors)
                closing_reading = _to_decimal(fuel_sale_data.get("closing_reading"), f"{prefix}.closing_reading", errors)
                testing_qty = _to_decimal(fuel_sale_data.get("testing_qty", 0), f"{prefix}.testing_qty", errors, required=False)
                rate_per_liter = _to_decimal(fuel_sale_data.get("rate_per_liter"), f"{prefix}.rate_per_liter", errors)

                total_qty = closing_reading - opening_reading
                if total_qty < DECIMAL_ZERO:
                    errors.append(f"{prefix}.closing_reading cannot be less than opening_reading")

                sale_qty = total_qty - testing_qty
                if sale_qty < DECIMAL_ZERO:
                    errors.append(f"{prefix}.testing_qty cannot be greater than total_qty")

                amount = sale_qty * rate_per_liter
                total_fuel_sales += amount

                fuel_sales.append({
                    "fuel_type": fuel_type,
                    "opening_reading": opening_reading,
                    "closing_reading": closing_reading,
                    "testing_qty": testing_qty,
                    "rate_per_liter": rate_per_liter,
                    "total_qty": total_qty,
                    "sale_qty": sale_qty,
                    "amount": amount,
                })

        cash = _to_decimal(collection_data.get("cash", 0), "collection.cash", errors, required=False)
        qr = _to_decimal(collection_data.get("qr", 0), "collection.qr", errors, required=False)
        card = _to_decimal(collection_data.get("card", 0), "collection.card", errors, required=False)
        credit = _to_decimal(collection_data.get("credit", 0), "collection.credit", errors, required=False)
        total_collection = cash + qr + card + credit

        expenses = []
        total_expenses = DECIMAL_ZERO
        for index, expense_data in enumerate(expenses_data):
            prefix = f"expenses[{index}]"
            if not isinstance(expense_data, dict):
                errors.append(f"{prefix} must be an object")
                continue

            expense_name = expense_data.get("expense_name")
            if not expense_name:
                errors.append(f"{prefix}.expense_name is required")

            amount = _to_decimal(expense_data.get("amount"), f"{prefix}.amount", errors)
            total_expenses += amount
            expenses.append({"expense_name": expense_name, "amount": amount})

        note_500 = _to_int(denomination_data.get("note_500", 0), "denomination.note_500", errors)
        note_200 = _to_int(denomination_data.get("note_200", 0), "denomination.note_200", errors)
        note_100 = _to_int(denomination_data.get("note_100", 0), "denomination.note_100", errors)
        note_50 = _to_int(denomination_data.get("note_50", 0), "denomination.note_50", errors)
        note_20 = _to_int(denomination_data.get("note_20", 0), "denomination.note_20", errors)
        note_10 = _to_int(denomination_data.get("note_10", 0), "denomination.note_10", errors)
        coins = _to_decimal(denomination_data.get("coins", 0), "denomination.coins", errors, required=False)

        actual_cash = (
            Decimal(note_500 * 500)
            + Decimal(note_200 * 200)
            + Decimal(note_100 * 100)
            + Decimal(note_50 * 50)
            + Decimal(note_20 * 20)
            + Decimal(note_10 * 10)
            + coins
        )
        expected_cash = cash - total_expenses

        if errors:
            response = response_translator.error_response(message=", ".join(errors))
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            receipt = ReceiptMaster.objects.create(
                receipt_date=receipt_date,
                shift=shift,
                operator=operator,
                total_fuel_sales=total_fuel_sales,
                total_collection=total_collection,
                total_expenses=total_expenses,
                expected_cash=expected_cash,
                actual_cash=actual_cash,
                created_by=operator,
                updated_by=operator,
            )

            ReceiptFuelSale.objects.bulk_create([
                ReceiptFuelSale(receipt=receipt, **fuel_sale)
                for fuel_sale in fuel_sales
            ])

            ReceiptCollection.objects.create(
                receipt=receipt,
                cash=cash,
                qr=qr,
                card=card,
                credit=credit,
                total_collection=total_collection,
            )

            ReceiptExpense.objects.bulk_create([
                ReceiptExpense(receipt=receipt, **expense)
                for expense in expenses
            ])

            ReceiptDenomination.objects.create(
                receipt=receipt,
                note_500=note_500,
                note_200=note_200,
                note_100=note_100,
                note_50=note_50,
                note_20=note_20,
                note_10=note_10,
                coins=coins,
                total_cash=actual_cash,
            )

        receipt = (
            ReceiptMaster.objects
            .select_related("operator", "collection", "denomination")
            .prefetch_related("fuel_sales", "expenses")
            .get(id=receipt.id)
        )
        response = response_translator.success_response(
            data=_receipt_data(receipt),
            message=success_msg.RECEIPT_CREATED_SUCCESSFULLY
        )
        return Response(response, status=status.HTTP_201_CREATED)

    except Exception as e:
        raise e


def update_receipt(request):
    request_data = request.data
    receipt_id = request_data.get("receipt_id")
    if not receipt_id:
        return Response(
            response_translator.error_response(message="receipt_id is required"),
            status=status.HTTP_400_BAD_REQUEST,
        )

    receipts = _filter_receipts_for_user(
        ReceiptMaster.objects.filter(is_active=True, is_deleted=False),
        request.user,
    )
    receipt = receipts.filter(id=receipt_id).first()
    if not receipt:
        return Response(
            response_translator.error_response(message=error_msg.RECEIPT_NOT_FOUND),
            status=status.HTTP_404_NOT_FOUND,
        )

    errors = []
    shift = request_data.get("shift", receipt.shift)
    if shift not in {choice[0] for choice in ReceiptMaster.SHIFT_CHOICES}:
        errors.append("shift must be MORNING, EVENING, or NIGHT")

    operator = receipt.operator
    if "operator_id" in request_data:
        operator = _get_operator(request, request_data)
        if not operator:
            errors.append("operator not found or permission denied")

    fuel_sales = None
    if "fuel_sales" in request_data:
        fuel_sales_data = request_data.get("fuel_sales")
        fuel_sales = []
        seen = set()
        if not isinstance(fuel_sales_data, list) or not fuel_sales_data:
            errors.append("fuel_sales must contain at least one item")
        else:
            valid_types = {choice[0] for choice in ReceiptFuelSale.FUEL_TYPE_CHOICES}
            for index, item in enumerate(fuel_sales_data):
                prefix = f"fuel_sales[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                fuel_type = item.get("fuel_type")
                if fuel_type not in valid_types:
                    errors.append(f"{prefix}.fuel_type must be PETROL or DIESEL")
                elif fuel_type in seen:
                    errors.append(f"{prefix}.fuel_type is duplicated")
                seen.add(fuel_type)
                opening = _to_decimal(item.get("opening_reading"), f"{prefix}.opening_reading", errors)
                closing = _to_decimal(item.get("closing_reading"), f"{prefix}.closing_reading", errors)
                testing = _to_decimal(item.get("testing_qty", 0), f"{prefix}.testing_qty", errors, False)
                rate = _to_decimal(item.get("rate_per_liter"), f"{prefix}.rate_per_liter", errors)
                total_qty = closing - opening
                sale_qty = total_qty - testing
                if total_qty < DECIMAL_ZERO:
                    errors.append(f"{prefix}.closing_reading cannot be less than opening_reading")
                if sale_qty < DECIMAL_ZERO:
                    errors.append(f"{prefix}.testing_qty cannot be greater than total_qty")
                fuel_sales.append({"fuel_type": fuel_type, "opening_reading": opening,
                    "closing_reading": closing, "testing_qty": testing, "rate_per_liter": rate,
                    "total_qty": total_qty, "sale_qty": sale_qty, "amount": sale_qty * rate})

    collection = None
    if "collection" in request_data:
        item = request_data.get("collection")
        if not isinstance(item, dict):
            errors.append("collection must be an object")
        else:
            collection = {key: _to_decimal(item.get(key, 0), f"collection.{key}", errors, False)
                          for key in ("cash", "qr", "card", "credit")}

    expenses = None
    if "expenses" in request_data:
        items = request_data.get("expenses")
        expenses = []
        if not isinstance(items, list):
            errors.append("expenses must be a list")
        else:
            for index, item in enumerate(items):
                prefix = f"expenses[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                name = item.get("expense_name")
                if not name:
                    errors.append(f"{prefix}.expense_name is required")
                expenses.append({"expense_name": name, "amount": _to_decimal(item.get("amount"), f"{prefix}.amount", errors)})

    denomination = None
    if "denomination" in request_data:
        item = request_data.get("denomination")
        if not isinstance(item, dict):
            errors.append("denomination must be an object")
        else:
            denomination = {key: _to_int(item.get(key, 0), f"denomination.{key}", errors)
                            for key in ("note_500", "note_200", "note_100", "note_50", "note_20", "note_10")}
            denomination["coins"] = _to_decimal(item.get("coins", 0), "denomination.coins", errors, False)

    if errors:
        return Response(response_translator.error_response(message=", ".join(errors)), status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        receipt.receipt_date = request_data.get("receipt_date", receipt.receipt_date)
        receipt.shift = shift
        receipt.operator = operator
        receipt.updated_by = request.user
        if fuel_sales is not None:
            receipt.fuel_sales.all().delete()
            ReceiptFuelSale.objects.bulk_create([ReceiptFuelSale(receipt=receipt, **item) for item in fuel_sales])
        if collection is not None:
            collection["total_collection"] = sum(collection.values(), DECIMAL_ZERO)
            ReceiptCollection.objects.update_or_create(receipt=receipt, defaults=collection)
        if expenses is not None:
            receipt.expenses.all().delete()
            ReceiptExpense.objects.bulk_create([ReceiptExpense(receipt=receipt, **item) for item in expenses])
        if denomination is not None:
            denomination["total_cash"] = sum(
                Decimal(denomination[key] * value) for key, value in
                (("note_500", 500), ("note_200", 200), ("note_100", 100), ("note_50", 50), ("note_20", 20), ("note_10", 10))
            ) + denomination["coins"]
            ReceiptDenomination.objects.update_or_create(receipt=receipt, defaults=denomination)

        receipt.total_fuel_sales = sum((item.amount for item in receipt.fuel_sales.all()), DECIMAL_ZERO)
        receipt.total_collection = receipt.collection.total_collection
        receipt.total_expenses = sum((item.amount for item in receipt.expenses.all()), DECIMAL_ZERO)
        receipt.expected_cash = receipt.collection.cash - receipt.total_expenses
        receipt.actual_cash = receipt.denomination.total_cash
        receipt.save()

    receipt = (ReceiptMaster.objects.select_related("operator", "collection", "denomination")
               .prefetch_related("fuel_sales", "expenses").get(id=receipt.id))
    return Response(response_translator.success_response(
        data=_receipt_data(receipt), message=success_msg.RECEIPT_UPDATED_SUCCESSFULLY
    ), status=status.HTTP_200_OK)


def get_receipts(request):
    try:
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        search_text = request.query_params.get("search_text") or request.query_params.get("search")
        selected_date = (
            request.query_params.get("selected_date")
            or request.query_params.get("receipt_date")
        )
        shift = request.query_params.get("shift")
        receipt_status = request.query_params.get("status")

        receipts = (
            ReceiptMaster.objects
            .filter(is_active=True, is_deleted=False)
            .select_related("operator")
            .order_by("-id")
        )
        receipts = _filter_receipts_for_user(receipts, request.user)

        if search_text:
            receipts = receipts.filter(
                Q(receipt_no__icontains=search_text)
                | Q(operator__username__icontains=search_text)
                | Q(operator__first_name__icontains=search_text)
                | Q(operator__last_name__icontains=search_text)
            )

        if selected_date:
            receipts = receipts.filter(receipt_date=selected_date)

        if shift:
            receipts = receipts.filter(shift__iexact=shift.strip())

        if receipt_status:
            receipts = receipts.filter(status__iexact=receipt_status.strip())

        total_count = receipts.count()
        summary_data = _summary_data(receipts)
        paginated_receipts = receipts[offset:offset + limit]

        response = response_translator.success_response(
            data={
                "summary_data": summary_data,
                "receipts": [_receipt_list_data(receipt) for receipt in paginated_receipts],
            },
            message=success_msg.RECEIPT_LIST_FETCHED,
            total_count=total_count
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e


def get_receipt_detail(request):
    try:
        receipt_id = request.query_params.get("receipt_id")
        receipt_no = request.query_params.get("receipt_no")

        if not receipt_id and not receipt_no:
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        receipts = (
            ReceiptMaster.objects
            .filter(is_active=True, is_deleted=False)
            .select_related(
                "operator",
                "operator__fuel_station",
                "collection",
                "denomination",
            )
            .prefetch_related("fuel_sales", "expenses")
        )
        receipts = _filter_receipts_for_user(receipts, request.user)

        if receipt_id:
            receipt = receipts.filter(id=receipt_id).first()
        else:
            receipt = receipts.filter(receipt_no=receipt_no).first()

        if not receipt:
            response = response_translator.error_response(message=error_msg.RECEIPT_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        response = response_translator.success_response(
            data=_receipt_detail_data(receipt),
            message=success_msg.RECEIPT_DETAIL_FETCHED
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e
