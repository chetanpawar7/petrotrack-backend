from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from user import helper
from user.authentication import SupabaseAuthentication
from utils import error_msg, logger_utils, success_msg, response_translator
# Create your views here.

class UserListView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info(f"Userlist Api Started....",request.data)
            return helper.get_user_list(request)   
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger_utils.main_info('Register User Api Started....', request.data)
            return helper.register_user(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger_utils.main_info('Login User Api Started....', {"email": request.data.get("email")})
            return helper.login_user(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutUserView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Logout User Api Started....', {"user_id": getattr(request.user, "id", None)})
            return helper.logout_user(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UpdateUserView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Update User Api Started....', request.data)
            return helper.update_user(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
