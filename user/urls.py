from django.urls import path
from user import views as user_views

urlpatterns = [
    path('user-list/', user_views.UserListView.as_view(), name='user_list'),
    path('register-user/', user_views.RegisterUserView.as_view(), name='register_user'),
    path('update-user/', user_views.UpdateUserView.as_view(), name='update_user')
]
    