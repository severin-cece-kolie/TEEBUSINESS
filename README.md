# TEEBUSINESS - E-commerce Django Project

Projet e-commerce Django avec système de sécurité avancé, authentification OTP, et gestion de newsletter.

## 🚀 Fonctionnalités

### Sécurité
- ✅ Authentification avec OTP (6 chiffres)
- ✅ Protection contre brute-force (5 tentatives = verrouillage 15 min)
- ✅ Vérification email requise après 10 tentatives
- ✅ Journalisation des événements de sécurité
- ✅ Cookies sécurisés et HTTPOnly
- ✅ En-têtes de sécurité (HSTS, X-Frame-Options, etc.)
- ✅ Rate limiting

### Email & Communication
- ✅ Système de newsletter complet
- ✅ Campagnes email avec tracking
- ✅ Support multiple backends (Gmail, SendGrid, Mailgun, SES, Brevo)
- ✅ Templates HTML personnalisés
- ✅ Historique des emails

### Admin Django
- ✅ Interface admin complète pour tous les modèles
- ✅ Actions en masse (activation, export, envoi)
- ✅ Gestion des abonnés newsletter
- ✅ Gestion des campagnes email
- ✅ Logs de sécurité

## 📋 Prérequis

- Python 3.8+
- pip
- virtualenv (optionnel)

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd TEEBUSINES
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

### 5. Exécuter les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 7. Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

### 8. Démarrer le serveur
```bash
python manage.py runserver
```

## 🔧 Configuration

### Variables d'environnement essentielles

```bash
# Django
DEBUG=False
SECRET_KEY=votre-secret-key
DJANGO_ALLOWED_HOSTS=votre-domaine.com

# Email
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password

# Sécurité
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Business
BUSINESS_NAME=TEEBUSINESS
BUSINESS_EMAIL=supportteebusiness@gmail.com
BUSINESS_PHONE=+224 623 70 78 33
```

## 📊 Structure du Projet

```
TEEBUSINES/
├── accounts/              # Authentification & Sécurité
│   ├── models.py         # User, OTP, LoginSecurityLog
│   ├── views.py          # Login, Register, OTP verification
│   ├── forms.py          # Formulaires d'authentification
│   ├── middleware.py     # Rate limiting, Security headers
│   └── utils.py          # OTP generation, Security logging
├── communication/         # Newsletter & Email
│   ├── models.py         # NewsletterSubscriber, EmailCampaign
│   ├── admin.py          # Interface admin
│   ├── tasks.py          # Email sending tasks
│   └── views.py          # Newsletter subscription
├── shop/                 # Catalogue produits
├── cart/                 # Panier
├── pages/                # Pages statiques
├── teebusiness_core/     # Configuration Django
│   ├── settings.py       # Settings principaux
│   └── urls.py          # URL routing
├── templates/            # Templates HTML
├── static/              # Fichiers statiques
├── media/               # Fichiers médias
└── requirements.txt     # Dépendances Python
```

## 🔐 Sécurité

### Authentification OTP
- Code à 6 chiffres envoyé par email
- Expiration après 10 minutes
- Limite de 5 renvois
- Compte inactif jusqu'à vérification

### Protection contre les attaques
- Verrouillage après 5 tentatives échouées
- Vérification email requise après 10 tentatives
- Rate limiting sur login et OTP resend
- Détection d'activités suspectes

### Cookies & Sessions
- HTTPOnly activé
- Secure en production
- SameSite: Lax
- Expiration: 30 jours (remember-me)

## 📧 Email

### Backends supportés
- **Gmail SMTP** (configuré par défaut)
- **SendGrid**
- **Mailgun**
- **Amazon SES**
- **Brevo**

### Configuration
Changer `EMAIL_BACKEND` dans `.env`:
- `console` - Développement
- `smtp` - Gmail/Brevo
- `sendgrid` - SendGrid
- `mailgun` - Mailgun
- `ses` - Amazon SES

## 🚢 Déploiement

### PythonAnywhere
Voir `PYTHONANYWHERE_DEPLOYMENT.md` pour les instructions détaillées.

### Étapes générales
1. Configurer les variables d'environnement
2. Configurer la base de données (PostgreSQL recommandé)
3. Exécuter les migrations
4. Collecter les fichiers statiques
5. Configurer SSL
6. Tester toutes les fonctionnalités

## 📝 Documentation

- `SECURITY_SETUP.md` - Configuration de sécurité détaillée
- `PYTHONANYWHERE_DEPLOYMENT.md` - Guide de déploiement PythonAnywhere
- `.env.example` - Template de configuration

## 🧪 Test

### Test local
```bash
python manage.py runserver
```

### Test email
```bash
# Dans .env
EMAIL_BACKEND=console
python manage.py runserver
```

## 🤝 Support

Pour toute question ou problème:
- Vérifiez les logs Django
- Consultez la documentation Django
- Contactez l'équipe de développement

## 📄 Licence

Propriété de TEEBUSINESS. Tous droits réservés.
