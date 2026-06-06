from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('search/', views.search, name='search'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('set-currency/', views.set_currency, name='set_currency'),
]
