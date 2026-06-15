from django.urls import path

from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('produits/', views.produits, name='produits'),
    path('commandes/', views.commandes, name='commandes'),
    path('clients/', views.clients, name='clients'),
    path('analyses/', views.analyses, name='analyses'),
    path('rapports/', views.rapports, name='rapports'),
    path('parametres/', views.parametres, name='parametres'),
    path('export/commandes.csv', views.export_orders_csv, name='export_orders'),
    path('export/produits.csv', views.export_products_csv, name='export_products'),
]
