from django.db import transaction
from django.db.models import Q
from user.models import FuelStationMaster, UserMaster, RoleMaster, SubRoleMaster, PageMaster, PageDetail
from user.serializer import UserListSerializer
from utils import error_msg, success_msg, response_translator, regex_utils, constants
from rest_framework.response import Response
from rest_framework import status
from user import db_helper

def get_user_list(request):
    try:
        request_data = request.data
        limit = request_data.get("limit", 10)
        offset = request_data.get("offset", 0)
        fuel_station_id = request_data.get("fuel_station_id")
        search_text = request_data.get('search_text',None)
        request_user = request.user
        
        user_data = UserMaster.objects.select_related("role", "sub_role", "fuel_station")

        if request_user.is_admin:
            if fuel_station_id:
                user_data = user_data.filter(fuel_station_id=fuel_station_id)
        elif request_user.is_manager:
            user_data = user_data.filter(
                fuel_station_id=request_user.fuel_station_id,
                role__role_name__iexact="OPERATOR",
            )
        else:
            user_data = user_data.filter(id=request_user.id)
        
        if search_text:
            user_data = user_data.filter(
                Q(username__icontains=search_text) |
                Q(first_name__icontains=search_text) |
                Q(last_name__icontains=search_text) |
                Q(email__icontains=search_text)
            )

        user_data = user_data.order_by('-updated_at')
        total_count = user_data.count()
        user_data = user_data[offset:offset + limit]
        serialized_data = UserListSerializer(user_data, many=True).data
        response = response_translator.success_response(data=serialized_data, message=success_msg.USER_LIST_FETCHED, total_count=total_count)
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        raise e


def get_user_profile(request):
    try:
        user_obj = (
            UserMaster.objects
            .filter(id=request.user.id, is_active=True)
            .select_related("role", "sub_role", "fuel_station")
            .first()
        )
        if not user_obj:
            response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        serialized_data = UserListSerializer(user_obj).data
        serialized_data["address"] = user_obj.address
        serialized_data["supabase_user_id"] = str(user_obj.supabase_user_id) if user_obj.supabase_user_id else None
        serialized_data["role_id"] = user_obj.role_id
        serialized_data["sub_role_id"] = user_obj.sub_role_id
        serialized_data["fuel_station_id"] = user_obj.fuel_station_id
        serialized_data["station_address"] = user_obj.fuel_station.address if user_obj.fuel_station else None
        serialized_data["station_pincode"] = user_obj.fuel_station.pincode if user_obj.fuel_station else None

        response = response_translator.success_response(
            data=serialized_data,
            message=success_msg.USER_PROFILE_FETCHED
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e


def register_user(request):
    try:
        request_data = request.data
        email = request_data.get("email")
        first_name = request_data.get("first_name")
        last_name = request_data.get("last_name")
        mobile_number = request_data.get("mobile_number")
        password = request_data.get("password")
        role_name = request_data.get("role_name", "Manager")
        sub_role_name = request_data.get("sub_role_name")
        station_name = request_data.get("station_name")
        stn_address = request_data.get("stn_address")
        stn_pincode = request_data.get("stn_pincode")
        user_address = request_data.get("user_address")

        if not all([email, first_name, last_name, mobile_number, password, role_name, station_name, stn_address, stn_pincode, user_address]):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        username = regex_utils.get_username_from_email(email)
        if not username:
            response = response_translator.error_response(message=error_msg.INVALID_EMAIL)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        role_obj = RoleMaster.objects.filter(role_name__iexact=role_name,is_active=True).first()
        if not role_obj:
            response = response_translator.error_response(message=error_msg.ROLE_NOT_FOUND)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


        sub_role_obj = None
        if sub_role_name:
            sub_role_obj = SubRoleMaster.objects.filter(
                sub_role_name__iexact=sub_role_name,
                role=role_obj,
                is_active=True
            ).first()
            if not sub_role_obj:
                response = response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        elif role_obj.role_name.upper() != "MANAGER":
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if UserMaster.objects.filter(
            Q(username=username) | Q(email=email) | Q(mobile_number=mobile_number),
            is_active=True
        ).exists():
            response = response_translator.error_response(message=error_msg.USER_ALREADY_EXISTS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        supabase_user = db_helper.create_supabase_user(email, password)
        supabase_user_id = db_helper.get_supabase_user_id(supabase_user)
        if not supabase_user_id:
            response = response_translator.error_response(message=error_msg.USER_CREATION_FAILED)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            fuel_stn_obj, _  = FuelStationMaster.objects.get_or_create(
                station_name=station_name,  
                defaults={'address': stn_address, 'pincode': stn_pincode, 'is_active': True}
                )

            user_obj = UserMaster.objects.create(
                supabase_user_id=supabase_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_number=mobile_number,
                role=role_obj,
                sub_role=sub_role_obj,
                fuel_station=fuel_stn_obj,
                address=user_address,
                is_active=True
            )

        response = response_translator.success_response(
            data={"user_id": user_obj.id, "supabase_user_id": supabase_user_id},
            message=success_msg.USER_REGISTRATION_SUCCESS
        )
        return Response(response, status=status.HTTP_201_CREATED)

    except Exception as e:
        raise e


def create_user(request):
    try:
        request_data = request.data
        request_user = request.user
        email = request_data.get("email")
        first_name = request_data.get("first_name")
        last_name = request_data.get("last_name")
        mobile_number = request_data.get("mobile_number")
        password = request_data.get("password")
        role_name = request_data.get("role_name")
        user_address = request_data.get("user_address") or request_data.get("address")
        fuel_station_id = request_data.get("fuel_station_id")

        if not request_user.is_admin and not request_user.is_manager:
            response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if not all([email, first_name, last_name, mobile_number, role_name, user_address]):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        username = regex_utils.get_username_from_email(email)
        if not username:
            response = response_translator.error_response(message=error_msg.INVALID_EMAIL)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        role_obj = RoleMaster.objects.filter(role_name__iexact=role_name, is_active=True).first()
        if not role_obj or role_obj.role_name.upper() not in ["OPERATOR", "MANAGER"]:
            response = response_translator.error_response(message=error_msg.ROLE_NOT_FOUND)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if role_obj.role_name.upper() == "MANAGER" and not password:
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if UserMaster.objects.filter(
            Q(username=username) | Q(email=email) | Q(mobile_number=mobile_number),
            is_active=True
        ).exists():
            response = response_translator.error_response(message=error_msg.USER_ALREADY_EXISTS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if request_user.is_manager:
            fuel_stn_obj = request_user.fuel_station
            if not fuel_stn_obj:
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not fuel_station_id:
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            try:
                fuel_station_id = int(fuel_station_id)
            except (TypeError, ValueError):
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            fuel_stn_obj = FuelStationMaster.objects.filter(id=fuel_station_id, is_active=True).first()
            if not fuel_stn_obj:
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        supabase_user_id = None
        if role_obj.role_name.upper() == "MANAGER":
            supabase_user = db_helper.create_supabase_user(email, password)
            supabase_user_id = db_helper.get_supabase_user_id(supabase_user)
            if not supabase_user_id:
                response = response_translator.error_response(message=error_msg.USER_CREATION_FAILED)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user_obj = UserMaster.objects.create(
                supabase_user_id=supabase_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                mobile_number=mobile_number,
                role=role_obj,
                fuel_station=fuel_stn_obj,
                address=user_address,
                is_active=True,
                created_by=request_user,
                updated_by=request_user,
            )

        serialized_data = UserListSerializer(user_obj).data
        serialized_data["supabase_user_id"] = str(user_obj.supabase_user_id) if user_obj.supabase_user_id else None
        serialized_data["fuel_station_id"] = user_obj.fuel_station_id

        response = response_translator.success_response(
            data=serialized_data,
            message=success_msg.USER_CREATED_SUCCESSFULLY
        )
        return Response(response, status=status.HTTP_201_CREATED)

    except Exception as e:
        raise e


def login_user(request):
    try:
        request_data = request.data
        email = request_data.get("email")
        password = request_data.get("password")

        if not all([email, password]):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        username = regex_utils.get_username_from_email(email)
        if not username:
            response = response_translator.error_response(message=error_msg.INVALID_EMAIL)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        auth_response = db_helper.login_supabase_user(email, password)
        supabase_user_id = db_helper.get_supabase_user_id(auth_response)
        session_data = db_helper.get_supabase_session_data(auth_response)
        if not supabase_user_id or not session_data or not session_data.get("access_token"):
            response = response_translator.error_response(message=error_msg.INVALID_CREDENTIALS)
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        user_obj = UserMaster.objects.filter(
            Q(supabase_user_id=supabase_user_id) | Q(email=email),
            is_active=True
        ).select_related("role", "sub_role", "fuel_station").first()
        if not user_obj:
            response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        data = {
            "user": {
                "id": user_obj.id,
                "supabase_user_id": str(user_obj.supabase_user_id) if user_obj.supabase_user_id else supabase_user_id,
                "username": user_obj.username,
                "first_name": user_obj.first_name,
                "last_name": user_obj.last_name,
                "email": user_obj.email,
                "mobile_number": user_obj.mobile_number,
                "role_name": user_obj.role.role_name if user_obj.role else None,
                "sub_role_name": user_obj.sub_role.sub_role_name if user_obj.sub_role else None,
                "station_name": user_obj.fuel_station.station_name if user_obj.fuel_station else None,
            },
            "auth": session_data
        }

        response = response_translator.success_response(
            data=data,
            message=success_msg.USER_LOGIN_SUCCESS
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e


def logout_user(request):
    try:
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        access_token = auth_header.split()[1] if auth_header else None

        if not access_token:
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        is_logged_out = db_helper.logout_supabase_user(access_token)
        if not is_logged_out:
            response = response_translator.error_response(message=error_msg.USER_LOGOUT_FAILED)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        response = response_translator.success_response(
            data={},
            message=success_msg.USER_LOGOUT_SUCCESS
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e
    

def update_user(request):
    try:
        request_data = request.data
        user_id = request_data.get("user_id")

        if not user_id:
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        request_user = request.user
        user_obj = (
            UserMaster.objects
            .filter(id=user_id)
            .select_related("role", "sub_role", "fuel_station")
            .first()
        )
        if not user_obj:
            response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        if request_user.is_manager:
            can_update_user = user_obj.is_operator and user_obj.fuel_station_id == request_user.fuel_station_id
        elif request_user.is_admin:
            can_update_user = True
        else:
            can_update_user = user_obj.id == request_user.id

        if not can_update_user:
            response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        email = request_data.get("email")
        username = request_data.get("username")
        mobile_number = request_data.get("mobile_number")
        role_name = request_data.get("role_name")
        sub_role_name = request_data.get("sub_role_name")
        fuel_station_id = request_data.get("fuel_station_id")
        station_name = request_data.get("station_name")
        stn_address = request_data.get("stn_address")
        stn_pincode = request_data.get("stn_pincode")

        if fuel_station_id:
            try:
                fuel_station_id = int(fuel_station_id)
            except (TypeError, ValueError):
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if email:
            email_username = regex_utils.get_username_from_email(email)
            if not email_username:
                response = response_translator.error_response(message=error_msg.INVALID_EMAIL)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            username = username or email_username

        duplicate_filter = Q()
        if email:
            duplicate_filter |= Q(email=email)
        if username:
            duplicate_filter |= Q(username=username)
        if mobile_number:
            duplicate_filter |= Q(mobile_number=mobile_number)

        if duplicate_filter and UserMaster.objects.filter(duplicate_filter, is_active=True).exclude(id=user_obj.id).exists():
            response = response_translator.error_response(message=error_msg.USER_ALREADY_EXISTS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        role_obj = None
        if role_name:
            role_obj = RoleMaster.objects.filter(role_name__iexact=role_name, is_active=True).first()
            if not role_obj:
                response = response_translator.error_response(message=error_msg.ROLE_NOT_FOUND)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        sub_role_obj = None
        if sub_role_name:
            sub_role_obj = SubRoleMaster.objects.filter(sub_role_name=sub_role_name, is_active=True).first()
            if not sub_role_obj:
                response = response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if request_user.is_manager and role_obj and role_obj.role_name.upper() != "OPERATOR":
            response = response_translator.error_response(message=error_msg.ROLE_NOT_FOUND)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        fuel_station_obj = None
        if request_user.is_manager and (fuel_station_id or station_name):
            if fuel_station_id and fuel_station_id != request_user.fuel_station_id:
                response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            if station_name and (
                not request_user.fuel_station
                or request_user.fuel_station.station_name.lower() != station_name.lower()
            ):
                response = response_translator.error_response(message=error_msg.USER_NOT_FOUND)
                return Response(response, status=status.HTTP_404_NOT_FOUND)
            fuel_station_obj = request_user.fuel_station
        elif fuel_station_id:
            fuel_station_obj = FuelStationMaster.objects.filter(id=fuel_station_id, is_active=True).first()
            if not fuel_station_obj:
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        elif station_name:
            fuel_station_obj = FuelStationMaster.objects.filter(station_name=station_name).first()
            if fuel_station_obj and not fuel_station_obj.is_active:
                response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if not fuel_station_obj:
                fuel_station_obj = FuelStationMaster.objects.create(
                    station_name=station_name,
                    address=stn_address,
                    pincode=stn_pincode,
                    is_active=True,
                    created_by=request_user,
                    updated_by=request_user,
                )

        allowed_fields = ["first_name", "last_name", "address"]
        if request_user.is_admin or request_user.is_manager:
            allowed_fields.append("is_active")
        with transaction.atomic():
            for field in allowed_fields:
                if field in request_data:
                    setattr(user_obj, field, request_data.get(field))

            if email:
                user_obj.email = email
            if username:
                user_obj.username = username
            if mobile_number:
                user_obj.mobile_number = mobile_number
            if role_obj and request_user.is_admin:
                user_obj.role = role_obj
            if sub_role_obj and (request_user.is_admin or request_user.is_manager):
                user_obj.sub_role = sub_role_obj
            if fuel_station_obj and (request_user.is_admin or request_user.is_manager):
                user_obj.fuel_station = fuel_station_obj

            if fuel_station_obj and (stn_address or stn_pincode):
                if stn_address:
                    fuel_station_obj.address = stn_address
                if stn_pincode:
                    fuel_station_obj.pincode = stn_pincode
                fuel_station_obj.updated_by = request_user
                fuel_station_obj.save()

            user_obj.updated_by = request_user
            user_obj.save()

        serialized_data = UserListSerializer(user_obj).data
        response = response_translator.success_response(
            data=serialized_data,
            message=success_msg.USER_UPDATE_SUCCESS
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e


def get_dropdown(request):
    try:
        dropdown_type = request.data.get("dropdown_type")

        try:
            limit = int(request.data.get("limit", 10))
            offset = int(request.data.get("offset", 0))
            if limit <= 0 or offset < 0:
                raise ValueError
        except (TypeError, ValueError):
            response = response_translator.error_response(
                message="limit must be greater than 0 and offset cannot be negative"
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        dropdown_handlers = {
            constants.USERS: get_dropdown_users,
            constants.ROLES: get_dropdown_roles,
        }
        handler = dropdown_handlers.get(dropdown_type)
        if handler is None:
            response = response_translator.error_response(
                message=error_msg.INVALID_DROPDOWN_TYPE
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        data, total_count = handler(request, limit, offset)
        response = response_translator.success_response(
            data=data,
            message=success_msg.DROPDOWN_FETCHED_SUCCESSFULLY,
            total_count=total_count,
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e


def get_dropdown_users(request, limit, offset):
    request_user = request.user
    search_text = str(request.data.get("search_text") or "").strip()
    users = UserMaster.objects.filter(is_active=True)

    if request_user.is_admin:
        fuel_station_id = request.data.get("fuel_station_id")
        if fuel_station_id:
            users = users.filter(fuel_station_id=fuel_station_id)
    elif request_user.is_manager:
        users = users.filter(
            fuel_station_id=request_user.fuel_station_id,
            role__role_name__iexact="OPERATOR",
        )
    else:
        users = users.filter(id=request_user.id)

    if search_text:
        users = users.filter(
            Q(first_name__icontains=search_text)
            | Q(last_name__icontains=search_text)
            | Q(username__icontains=search_text)
            | Q(email__icontains=search_text)
        )

    total_count = users.count()
    data = list(
        users.order_by("first_name", "last_name", "id").values(
            "id", "first_name", "last_name", "username"
        )[offset:offset + limit]
    )
    return data, total_count


def get_dropdown_roles(request, limit, offset):
    search_text = str(request.data.get("search_text") or "").strip()
    roles = RoleMaster.objects.filter(is_active=True)

    if request.user.is_manager:
        roles = roles.filter(
            Q(role_name__iexact="OPERATOR") | Q(role_name__iexact="MANAGER")
        )
    elif not request.user.is_admin:
        roles = roles.filter(id=request.user.role_id)

    if search_text:
        roles = roles.filter(role_name__icontains=search_text)

    total_count = roles.count()
    data = list(
        roles.order_by("role_name").values("id", "role_name")[offset:offset + limit]
    )
    return data, total_count


def get_page_perm(request):
    try:
        request_user = request.user
        try:
            limit = int(request.data.get("limit", 10))
            offset = int(request.data.get("offset", 0))
        except (TypeError, ValueError):
            return Response(
                response_translator.error_response(message="Invalid limit or offset"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit <= 0 or offset < 0:
            return Response(
                response_translator.error_response(message="Invalid limit or offset"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request_user.role_id:
            return Response(
                response_translator.error_response(message=error_msg.DATA_NOT_FOUND),
                status=status.HTTP_404_NOT_FOUND,
            )

        sub_role_filter = Q(sub_role_id=request_user.sub_role_id)
        if request_user.sub_role_id:
            # A null sub-role represents permissions shared by the whole role.
            sub_role_filter |= Q(sub_role__isnull=True)

        permissions = (
            PageDetail.objects.filter(
                Q(role_id=request_user.role_id),
                sub_role_filter,
                is_active=True,
                page__is_active=True,
            )
            .select_related("page", "page__parent")
            .order_by("page__display_order", "page_id", "control_type")
        )

        pages = {}
        for permission in permissions:
            page = permission.page
            page_data = pages.setdefault(
                page.id,
                {
                    "id": page.id,
                    "page_name": page.page_name,
                    "page_code": page.page_code,
                    "route_path": page.route_path,
                    "icon": page.icon,
                    "parent_id": page.parent_id,
                    "display_order": page.display_order,
                    "is_menu": page.is_menu,
                    "permissions": [],
                },
            )
            if permission.control_type not in page_data["permissions"]:
                page_data["permissions"].append(permission.control_type)

        page_list = list(pages.values())
        total_count = len(page_list)
        page_list = page_list[offset:offset + limit]

        response = response_translator.success_response(
            data=page_list,
            message=success_msg.PAGE_PERMISSIONS_FETCHED_SUCCESSFULLY,
            total_count=total_count,
        )
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        raise e
