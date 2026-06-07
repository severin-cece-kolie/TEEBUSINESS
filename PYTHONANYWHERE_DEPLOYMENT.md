# Déploiement sur PythonAnywhere

## Configuration pour PythonAnywhere

### 1. Configuration de l'environnement

Le projet est configuré pour le mode production avec:
- **DEBUG=False**
- **Cookies sécurisés activés**
- **HSTS activé**
- **SSL redirect activé**

### 2. Variables d'environnement à configurer sur PythonAnywhere

Dans le tableau de bord PythonAnywhere, allez dans:
`Web tab → Variables` et ajoutez:

```bash
DEBUG=False
SECRET_KEY=p023!0$)+=$8ktw6%54zj&hhsfx!y@&2rvy59#a17*!_rq!#+%
DJANGO_ALLOWED_HOSTS=teebusiness.pythonanywhere.com
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=supportteebusiness@gmail.com
EMAIL_HOST_PASSWORD=xjpc oslx kbki okzu
DEFAULT_FROM_EMAIL=supportteebusiness@gmail.com
SERVER_EMAIL=supportteebusiness@gmail.com
BUSINESS_NAME=TEEBUSINESS
BUSINESS_PHONE=+224 623 70 78 33
BUSINESS_EMAIL=supportteebusiness@gmail.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
RATELIMIT_ENABLE=True
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
REQUIRE_EMAIL_VERIFICATION_ATTEMPTS=10
OTP_EXPIRATION_MINUTES=10
OTP_RESEND_LIMIT=5
OTP_RESEND_COOLDOWN_MINUTES=2
```

### 3. Base de données

PythonAnywhere utilise PostgreSQL par défaut. Configurez:

```bash
# Dans Variables d'environnement
DATABASE_URL=postgresql://username:password@username.postgres.pythonanywhere-services.com/username$dbname
```

Ou modifiez `teebusiness_core/settings.py` pour utiliser PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'votre-nom-db',
        'USER': 'votre-username',
        'PASSWORD': 'votre-password',
        'HOST': 'username.postgres.pythonanywhere-services.com',
        'PORT': '5432',
    }
}
```

### 4. Fichiers statiques

Dans le `Web tab` de PythonAnywhere:

**Static files configuration:**
- URL: `/static/`
- Directory: `/home/username/TEEBUSINES/staticfiles`

Exécutez:
```bash
python manage.py collectstatic --noinput
```

### 5. Fichiers médias

**Media files configuration:**
- URL: `/media/`
- Directory: `/home/username/TEEBUSINES/media`

### 6. WSGI Configuration

Le fichier WSGI de PythonAnywhere devrait ressembler à:

```python
import os
import sys

path = '/home/username/TEEBUSINES'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'teebusiness_core.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Installation des dépendances

Dans le virtual environment de PythonAnywhere:

```bash
pip install -r requirements.txt
pip install python-dotenv
pip install psycopg2-binary  # Pour PostgreSQL
```

### 8. Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9. Création du superutilisateur

```bash
python manage.py createsuperuser
```

### 10. Configuration SSL

PythonAnywhere fournit SSL gratuit via Let's Encrypt:
- Activez SSL dans le `Web tab`
- Configurez votre domaine personnalisé si nécessaire

### 11. Worker Configuration

Dans le `Web tab`:
- **Worker type**: `wsgi`
- **Worker count**: 1-2 (selon votre plan)
- **Timeout**: 300 secondes

### 12. Logs

Vérifiez les logs dans:
- `Web tab → Logs` pour les erreurs HTTP
- `/var/log/` pour les logs système

### 13. Test après déploiement

1. Vérifiez que le site est accessible
2. Testez l'inscription avec OTP
3. Testez la connexion
4. Vérifiez l'admin Django
5. Testez la newsletter

### 14. Sécurité supplémentaire

- Changez la SECRET_KEY
- Utilisez des mots de passe forts
- Activez 2FA sur PythonAnywhere
- Configurez les backups automatiques

### 15. Monitoring

- Surveillez les logs d'erreurs
- Vérifiez les LoginSecurityLog dans l'admin
- Surveillez les EmailHistory pour les emails

## Dépannage

### Erreur 500
- Vérifiez les logs dans PythonAnywhere
- Assurez-vous que toutes les migrations sont appliquées
- Vérifiez les variables d'environnement

### Emails non envoyés
- Vérifiez la configuration SMTP
- Testez avec EMAIL_BACKEND=console temporairement
- Vérifiez les logs d'erreurs

### Problèmes de fichiers statiques
- Exécutez `collectstatic` à nouveau
- Vérifiez les permissions des dossiers
- Vérifiez la configuration dans le Web tab

## Support

Pour toute question, consultez la documentation PythonAnywhere ou Django.
