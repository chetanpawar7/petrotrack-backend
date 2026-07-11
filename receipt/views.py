from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from receipt import helper
from user.authentication import SupabaseAuthentication
from utils import error_msg, logger_utils, success_msg, response_translator
# Create your views here.

class CreateReceiptView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Create Receipt Api Started....', request.data)
            return helper.create_receipt(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReceiptsView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger_utils.main_info('Get Receipts Api Started....', request.query_params)
            return helper.get_receipts(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateReceiptView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logger_utils.main_info('Update Receipt Api Started....', request.data)
            return helper.update_receipt(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(), str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetReceiptDetailView(APIView):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger_utils.main_info('Get Receipt Detail Api Started....', request.query_params)
            return helper.get_receipt_detail(request)
        except Exception as e:
            logger_utils.main_exception(self.get_view_name(),str(e))
            return Response(response_translator.error_response(message=error_msg.INTERNAL_SERVER_ERROR), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
