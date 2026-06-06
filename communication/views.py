from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import NewsletterSubscriber
import json


@require_POST
@csrf_exempt
def newsletter_subscribe(request):
    """
    Handle newsletter subscription requests from the frontend.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        source = data.get('source', 'Website')
        
        # Validate that at least email or phone is provided
        if not email and not phone:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide either an email or phone number.'
            }, status=400)
        
        # Check if subscriber already exists
        if email:
            existing = NewsletterSubscriber.objects.filter(email=email).first()
            if existing:
                if existing.status == 'active':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'You are already subscribed to our newsletter!'
                    })
                else:
                    # Reactivate existing subscriber
                    existing.status = 'active'
                    existing.source = source
                    existing.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Your subscription has been reactivated!'
                    })
        
        if phone:
            existing = NewsletterSubscriber.objects.filter(phone_number=phone).first()
            if existing:
                if existing.status == 'active':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'You are already subscribed to our newsletter!'
                    })
                else:
                    # Reactivate existing subscriber
                    existing.status = 'active'
                    existing.source = source
                    existing.save()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Your subscription has been reactivated!'
                    })
        
        # Create new subscriber
        full_name = email.split('@')[0] if email else phone  # Use email username or phone as name
        subscriber = NewsletterSubscriber.objects.create(
            full_name=full_name,
            email=email if email else None,
            phone_number=phone if phone else None,
            source=source,
            status='active'  # Auto-activate for newsletter subscriptions
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you for subscribing to our newsletter!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred. Please try again.'
        }, status=500)
