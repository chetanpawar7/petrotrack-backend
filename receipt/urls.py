from django.urls import path
from receipt import views as receipt_views

urlpatterns = [
    path('create-receipt/', receipt_views.CreateReceiptView.as_view(), name='create_receipt'),
    path('get-receipts/', receipt_views.GetReceiptsView.as_view(), name='get_receipts'),
    path('get-receipt-detail/', receipt_views.GetReceiptDetailView.as_view(), name='get_receipt_detail'),
]
