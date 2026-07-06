from django.db import transaction
from django.db.models import Q
from user.models import FuelStationMaster, UserMaster, RoleMaster, SubRoleMaster
from user.serializer import UserListSerializer
from utils import error_msg, success_msg, response_translator, regex_utils
from rest_framework.response import Response
from rest_framework import status
from user import db_helper

def get_user_list(request):
    try:
        request_data = request.data
        limit = request_data.get("limit", 10)
        offset = request_data.get("offset", 0)
        fuel_station_id = request_data.get("fuel_station_id")
        request_user = request.user

        user_data = UserMaster.objects.filter(is_active=True).select_related("role", "sub_role", "fuel_station")

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

        user_data = user_data.order_by('-updated_at')
        total_count = user_data.count()
        user_data = user_data[offset:offset + limit]
        serialized_data = UserListSerializer(user_data, many=True).data
        response = response_translator.success_response(data=serialized_data, message=success_msg.USER_LIST_FETCHED, total_count=total_count)
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
        role_name = request_data.get("role_name")
        sub_role_name = request_data.get("sub_role_name")
        station_name = request_data.get("station_name")
        stn_address = request_data.get("stn_address")
        stn_pincode = request_data.get("stn_pincode")
        user_address = request_data.get("user_address")

        if not all([email, first_name, last_name, mobile_number, password, role_name, sub_role_name, station_name, stn_address, stn_pincode, user_address]):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        username = regex_utils.get_username_from_email(email)
        if not username:
            response = response_translator.error_response(message=error_msg.INVALID_EMAIL)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        role_obj = RoleMaster.objects.filter(role_name=role_name,is_active=True).first()
        if not role_obj:
            response = response_translator.error_response(message=error_msg.ROLE_NOT_FOUND)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


        sub_role_obj = SubRoleMaster.objects.filter(sub_role_name=sub_role_name,is_active=True).first()
        if not sub_role_obj:
            response = response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND)
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
    

def update_user(request):
    try:
        request_data = request.data
        user_id = request_data.get("user_id")
        

    except Exception as e:
        raise e
