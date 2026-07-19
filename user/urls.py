from django.urls import path
from user import views as user_views

urlpatterns = [
    path('user-list/', user_views.UserListView.as_view(), name='user_list'),
    path('get-user-profile/', user_views.GetUserProfileView.as_view(), name='get_user_profile'),
    path('create-station/', user_views.CreateStationView.as_view(), name='create_station'),
    path('create-user/', user_views.CreateUserView.as_view(), name='create_user'),
    path('login/', user_views.LoginUserView.as_view(), name='login_user'),
    path('logout/', user_views.LogoutUserView.as_view(), name='logout_user'),
    path('forgot-password/', user_views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('update-user/', user_views.UpdateUserView.as_view(), name='update_user'),
    path('get-dropdown/', user_views.GetDropDownApiView.as_view(), name='get-dropdown'),
    path('get-page-perm/',user_views.GetPagePermApiView.as_view(), name='get-page-list')
]
    
