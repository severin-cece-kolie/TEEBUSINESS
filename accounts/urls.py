from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('community-signup/', views.community_signup, name='community_signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('orders/', views.orders_view, name='orders'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-otp/<uuid:user_id>/', views.verify_otp_view, name='verify_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp_default'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
