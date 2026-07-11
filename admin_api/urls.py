from django.urls import path
from admin_api import views as admin_views


urlpatterns = [
    path('create-page/', admin_views.CreatePageView.as_view(), name='create_page'),
    path('assign-page-permissions/',admin_views.AssignPagePermissionsView.as_view(),name='assign_page_permissions',),
]
