import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from yoga_app.models import Course, Payment
from yoga_app.services import PaymentService

logger = logging.getLogger(__name__)


@login_required
def initiate_payment_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method != 'POST':
        messages.error(request, 'Invalid request method for payment initiation.')
        return redirect('home')

    # Block duplicate enrollment — redirect to course content if already enrolled
    from yoga_app.services import EnrollmentService
    if EnrollmentService.is_enrolled(request.user, course):
        messages.info(request, f"You are already enrolled in '{course.title}'.")
        return redirect('course_content_base', course_id=course.id)

    user_email = request.user.email
    if not user_email:
        user_email = f"{request.user.username}@example.com"
        messages.warning(
            request,
            "Your account has no email address. Please update your profile for accurate payment records."
        )

    payment_data = PaymentService.initiate_payment(request.user, course)

    context = {
        'course': course,
        'amount': payment_data['amount_kobo'],
        'email': payment_data['email'],
        'public_key': payment_data['public_key'],
        'metadata_json': payment_data['metadata_json'],
        'transaction_reference': payment_data['transaction_reference'],
    }
    return render(request, 'yoga_app/payment_initiate.html', context)


def verify_payment_view(request):
    if request.method != 'GET':
        messages.error(request, 'Invalid request for payment verification.')
        return redirect('home')

    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "Payment verification failed: no transaction reference provided.")
        return redirect('home')

    try:
        success, data = PaymentService.verify_payment(reference)
        if success:
            messages.success(request, "Payment successful! Your enrollment is being processed.")
            return redirect('dashboard')
        else:
            gateway_response = data.get('gateway_response', 'No specific response.')
            messages.error(request, f"Payment failed: {gateway_response}. Please try again.")
            return redirect('home')
    except Exception as e:
        logger.exception("Paystack verification failed for reference %s: %s", reference, e)
        messages.error(request, "Could not verify payment due to a network error. Please contact support.")
        return redirect('home')


@csrf_exempt
def paystack_webhook_view(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    paystack_signature = request.headers.get('x-paystack-signature', '')
    request_body = request.body.decode('utf-8')

    if not PaymentService.verify_webhook_signature(request_body, paystack_signature):
        logger.warning("Webhook rejected: invalid signature")
        return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

    try:
        event_data = json.loads(request_body)
    except json.JSONDecodeError:
        logger.warning("Webhook rejected: invalid JSON payload")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    try:
        success, message = PaymentService.process_webhook(event_data)
        if not success:
            logger.info("Webhook event not processed: %s", message)
        # Always return 200 to Paystack to prevent retries on business-logic non-errors
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.exception("Unexpected error processing webhook: %s", e)
        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)
