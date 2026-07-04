from django.db import transaction
from user.models import FuelStationMaster, UserMaster
from user.serializer import UserListSerializer
from utils import error_msg, success_msg, response_translator, regex_utils
from rest_framework.response import Response
from rest_framework import status

def get_user_list(request):
    try:
        request_data = request.data
        fuel_station_id = request_data.get("fuel_station_id",1)
        limit = request_data.get("limit", 10)
        offset = request_data.get("offset", 0)

        user_data = UserMaster.objects.filter(fuel_station_id=fuel_station_id, is_active=True).order_by('-updated_at')
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
        mobile_number = request_data.get("mobile_number")
        role_name = request_data.get("role_name")
        sub_role_name = request_data.get("sub_role_name")
        station_name = request_data.get("station_name")
        stn_address = request_data.get("stn_address")
        stn_pincode = request_data.get("stn_pincode")
        user_address = request_data.get("user_address")

        if not all([email, mobile_number, role_name, sub_role_name, station_name, stn_address, stn_pincode, user_address]):
            response = response_translator.error_response(message=error_msg.MISSING_REQUIRED_FIELDS)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            fuel_stn_obj, _  = FuelStationMaster.objects.get_or_create(
                station_name=station_name,  
                defaults={'address': stn_address, 'pincode': stn_pincode, 'is_active': True}
                ).first()
            
            username = regex_utils.get_username_from_email(email)
            # Check if the user already exists
            if UserMaster.objects.filter(
                username=username, email=email, mobile_number=mobile_number,fuel_station=fuel_stn_obj, is_active=True).exists():
                response = response_translator.error_response(message=error_msg.USER_ALREADY_EXISTS)
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            # Create a new user
            UserMaster.objects.create(
                username=username,
                email=email,
                mobile_number=mobile_number,
                role_id=role_name,
                sub_role_id=sub_role_name,
                fuel_station=fuel_stn_obj,
                address=user_address,
                is_active=True
            )

        return Response(response_translator.success_response(message=success_msg.USER_REGISTERED), status=status.HTTP_201_CREATED)

    except Exception as e:
        raise e
    

def update_user(request):
    try:
        request_data = request.data
        user_id = request_data.get("user_id")
        

    except Exception as e:
        raise e