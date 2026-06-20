from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('search/', views.search, name='search'),
    # Old numeric URLs (/product/10/) permanently redirect to the slug URL —
    # keeps existing links + SEO while removing guessable incremental IDs.
    path('product/<int:id>/', views.product_detail_redirect, name='product_detail_by_id'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('set-currency/', views.set_currency, name='set_currency'),
]
