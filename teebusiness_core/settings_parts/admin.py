"""Django Unfold and django-import-export configuration."""

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


UNFOLD = {
    "SITE_TITLE": "TEEBUSINESS Admin",
    "SITE_HEADER": "TEEBUSINESS",
    "SITE_SUBHEADER": "Panneau d'administration",
    "SITE_URL": "/",
    "SITE_LOGO": lambda request: static("assets/images/logo.png"),
    "SITE_ICON": lambda request: static("assets/images/logo.png"),
    "SITE_SYMBOL": "storefront",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "BORDER_RADIUS": "9px",
    "DASHBOARD_CALLBACK": "cart.admin.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "#fdf2f4", "100": "#fbe3e7", "200": "#f6c2cb", "300": "#ee94a3",
            "400": "#e25c72", "500": "#c5283d", "600": "#a4182b", "700": "#871322",
            "800": "#6f1320", "900": "#5f141f", "950": "#3f0d15",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {"title": _("Tableau de bord"), "separator": False, "items": [
                {"title": _("Vue d'ensemble"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
            ]},
            {"title": _("Boutique"), "separator": True, "items": [
                {"title": _("Commandes"), "icon": "shopping_cart", "link": reverse_lazy("admin:cart_order_changelist")},
                {"title": _("Produits"), "icon": "inventory_2", "link": reverse_lazy("admin:shop_product_changelist")},
                {"title": _("Stock & tailles"), "icon": "layers", "link": reverse_lazy("admin:shop_productsize_changelist")},
                {"title": _("Catégories"), "icon": "category", "link": reverse_lazy("admin:shop_category_changelist")},
                {"title": _("Marques"), "icon": "sell", "link": reverse_lazy("admin:shop_brand_changelist")},
            ]},
            {"title": _("Clients"), "separator": True, "items": [
                {"title": _("Utilisateurs"), "icon": "group", "link": reverse_lazy("admin:accounts_user_changelist")},
                {"title": _("Abonnés newsletter"), "icon": "mail", "link": reverse_lazy("admin:communication_newslettersubscriber_changelist")},
            ]},
            {"title": _("Communication"), "separator": True, "items": [
                {"title": _("Campagnes email"), "icon": "campaign", "link": reverse_lazy("admin:communication_emailcampaign_changelist")},
                {"title": _("Historique emails"), "icon": "history", "link": reverse_lazy("admin:communication_emailhistory_changelist")},
            ]},
            {"title": _("Sécurité"), "separator": True, "items": [
                {"title": _("Codes OTP"), "icon": "pin", "link": reverse_lazy("admin:accounts_otp_changelist")},
                {"title": _("Journaux de connexion"), "icon": "security", "link": reverse_lazy("admin:accounts_loginsecuritylog_changelist")},
                {"title": _("Groupes & rôles"), "icon": "admin_panel_settings", "link": reverse_lazy("admin:auth_group_changelist")},
            ]},
        ],
    },
}

IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_SKIP_ADMIN_LOG = False
