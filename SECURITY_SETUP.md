# TEEBUSINESS - Configuration de Sécurité et Email

## Configuration Terminée ✓

Votre système de sécurité et d'email est maintenant configuré et prêt à l'emploi.

## Configuration Email Actuelle

- **Backend**: SMTP (Gmail)
- **Email**: supportteebusiness@gmail.com
- **Hôte**: smtp.gmail.com
- **Port**: 587
- **TLS**: Activé

## Fonctionnalités de Sécurité Implémentées

### 1. Authentification avec OTP
- Les utilisateurs doivent vérifier leur email avec un code OTP à 6 chiffres
- Le code expire après 10 minutes
- Possibilité de renvoyer le code (limité à 5 tentatives)
- Le compte reste inactif jusqu'à la vérification

### 2. Protection contre les attaques
- **Verrouillage après 5 tentatives échouées**: Compte bloqué pendant 15 minutes
- **Vérification email requise après 10 tentatives**: Nécessite une nouvelle vérification
- **Limitation de taux**: Protection contre les attaques en masse
- **Journalisation des événements**: Tous les logins sont enregistrés

### 3. Sécurité des Cookies
- Cookies HTTPOnly activés
- Protection CSRF activée
- Cookies sécurisés en production
- SameSite configuré sur 'Lax'

### 4. En-têtes de Sécurité
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection activé
- HSTS en production

## Système de Newsletter

### Modèles Disponibles dans l'Admin Django

1. **NewsletterSubscriber**
   - Gestion des abonnés
   - Export en CSV
   - Activation en masse
   - Envoi d'emails de test

2. **EmailCampaign**
   - Création de campagnes email
   - Types: promotionnel, restock, nouveau produit, discount, annonce, newsletter
   - Suivi des statistiques (taux d'ouverture, taux de clic)
   - Planification des envois

3. **EmailHistory**
   - Historique complet des emails envoyés
   - Statut de livraison
   - Erreurs et échecs

4. **OTP**
   - Gestion des codes OTP
   - Invalidation en masse
   - Suppression des codes expirés

5. **LoginSecurityLog**
   - Journal des événements de sécurité
   - Détection d'activités suspectes
   - Historique des connexions

## Utilisation

### Démarrer le serveur
```bash
python manage.py runserver
```

### Accéder à l'Admin Django
```
URL: http://localhost:8000/admin/
Identifiant: cece
```

### Flow d'Inscription
1. Utilisateur s'inscrit avec username, email, mot de passe
2. Un code OTP est envoyé à son email
3. Utilisateur entre le code sur la page de vérification
4. Compte activé et utilisateur connecté automatiquement

### Flow de Connexion
1. Utilisateur entre username et mot de passe
2. Système vérifie si le compte est verrouillé
3. Si trop de tentatives échouées, compte bloqué temporairement
4. Connexion réussie réinitialise les tentatives

## Variables d'Environnement

Le fichier `.env` contient toutes les configurations essentielles:

- **DEBUG**: Mode développement (True/False)
- **SECRET_KEY**: Clé secrète Django
- **EMAIL_BACKEND**: Type de backend email (smtp, console, sendgrid, mailgun, ses, brevo)
- **EMAIL_HOST_USER**: Email d'envoi
- **EMAIL_HOST_PASSWORD**: Mot de passe de l'email
- **BUSINESS_EMAIL**: Email de contact de l'entreprise
- **BUSINESS_PHONE**: Téléphone de l'entreprise
- **MAX_LOGIN_ATTEMPTS**: Nombre max de tentatives avant verrouillage
- **LOCKOUT_DURATION**: Durée du verrouillage en secondes
- **OTP_EXPIRATION_MINUTES**: Durée de validité du code OTP

## Prochaines Étapes pour la Production

1. **Changer DEBUG=False** dans le fichier .env
2. **Générer une nouvelle SECRET_KEY** forte
3. **Configurer HTTPS** avec SSL
4. **Utiliser une base de données PostgreSQL** au lieu de SQLite
5. **Configurer Celery** pour les envois d'emails en arrière-plan
6. **Utiliser Redis** pour le cache
7. **Configurer un serveur de production** (Gunicorn, Nginx)

## Fournisseurs d'Email Disponibles

Le système supporte plusieurs fournisseurs:
- **Gmail SMTP** (configuré actuellement)
- **SendGrid**: Décommenter dans requirements.txt et configurer SENDGRID_API_KEY
- **Mailgun**: Décommenter dans requirements.txt et configurer MAILGUN_API_KEY
- **Amazon SES**: Décommenter dans requirements.txt et configurer AWS credentials
- **Brevo**: Configurer BREVO_API_KEY

Pour changer de fournisseur, modifiez `EMAIL_BACKEND` dans le fichier .env.

## Support

Pour toute question ou problème, consultez la documentation Django ou contactez l'équipe de développement.
