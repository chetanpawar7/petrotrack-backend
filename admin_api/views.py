from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from admin_api import helper
from user.authentication import SupabaseAuthentication
from utils import error_msg, logger_utils, response_translator


class CreatePageView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Create Page Api Started....', request.data)
            return helper.create_page(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(), str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignPagePermissionsView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Assign Page Permissions Api Started....', request.data)
            return helper.assign_page_permissions(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(), str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPageListView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Get Page List Api Started....', request.data)
            return helper.get_page_list(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(), str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
