import json
import uuid
import hmac
import hashlib
import logging
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import requests
from yoga_app.models import Payment, Course, User, UserProfile

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def initiate_payment(user, course):
        user_email = user.email or f"{user.username}@example.com"
        amount_kobo = int(course.price * 100)
        transaction_reference = str(uuid.uuid4())

        with transaction.atomic():
            payment = Payment.objects.create(
                user=user,
                course=course,
                amount=course.price,
                status='pending',
                reference=transaction_reference,
            )

        paystack_metadata = {
            'course_id': course.id,
            'payment_id': payment.id,
            'our_reference': transaction_reference,
            'user_id': user.id,
        }

        return {
            'course': course,
            'amount_kobo': amount_kobo,
            'email': user_email,
            'public_key': settings.PAYSTACK_PUBLIC_KEY,
            'metadata_json': json.dumps(paystack_metadata),
            'transaction_reference': transaction_reference,
            'payment': payment,
        }

    @staticmethod
    def verify_payment(reference):
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        verification_url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"

        response = requests.get(verification_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data['status'] and data['data']['status'] == 'success':
            # Also enroll the user here in case webhook was missed
            try:
                from yoga_app.models import Payment as PaymentModel
                payment = PaymentModel.objects.filter(reference=reference).first()
                if payment and payment.status != 'success':
                    payment.status = 'success'
                    from django.utils import timezone
                    payment.paid_at = timezone.now()
                    payment.verified_at = timezone.now()
                    payment.save(update_fields=['status', 'paid_at', 'verified_at'])
                if payment and payment.user and payment.course:
                    PaymentService._enroll_user(payment.user, payment.course)
            except Exception as e:
                logger.warning("Post-verify enrollment failed for ref %s: %s", reference, e)
            return True, data
        else:
            gateway_response = data['data'].get('gateway_response', 'No specific response.')
            return False, {'message': data.get('message', 'Payment failed'), 'gateway_response': gateway_response}

    @staticmethod
    def process_webhook(event_data):
        event_type = event_data.get('event')
        transaction_data = event_data.get('data')

        if event_type != 'charge.success' or not transaction_data:
            return False, "Not a charge.success event"

        paystack_reference = transaction_data.get('reference')
        status = transaction_data.get('status')
        amount_paid = transaction_data.get('amount') / 100
        customer_email = transaction_data.get('customer', {}).get('email')
        metadata = transaction_data.get('metadata', {})

        course_id_from_meta = metadata.get('course_id')
        user_id_from_meta = metadata.get('user_id')
        our_generated_reference_from_meta = metadata.get('our_reference')

        if status != 'success':
            return False, f"Payment status: {status}"

        try:
            with transaction.atomic():
                payment = PaymentService._find_or_create_payment(
                    our_generated_reference_from_meta,
                    paystack_reference,
                    course_id_from_meta,
                    user_id_from_meta,
                    customer_email,
                    amount_paid
                )

                if payment and payment.status != 'success':
                    payment.status = 'success'
                    payment.paid_at = timezone.now()
                    payment.verified_at = timezone.now()
                    payment.save(update_fields=['status', 'paid_at', 'verified_at', 'updated_at'])

                if payment and payment.user and payment.course:
                    PaymentService._enroll_user(payment.user, payment.course)

                return True, "Webhook processed successfully"
        except Exception as e:
            logger.exception("Webhook processing failed: %s", e)
            return False, f"Webhook processing failed: {str(e)}"

    @staticmethod
    def _find_or_create_payment(our_ref, paystack_ref, course_id, user_id, customer_email, amount_paid):
        payment = None

        if our_ref:
            payment = Payment.objects.filter(reference=our_ref).first()
            if payment:
                logger.info("Found Payment using our_reference: %s", our_ref)

        if not payment and paystack_ref:
            payment = Payment.objects.filter(reference=paystack_ref).first()
            if payment:
                logger.info("Found Payment using Paystack reference: %s", paystack_ref)

        if not payment:
            logger.info("No existing Payment found. Creating fallback for ref: %s", paystack_ref)
            course_obj = Course.objects.filter(id=course_id).first()
            user_obj = User.objects.filter(id=user_id).first()
            if not user_obj and customer_email:
                user_obj = User.objects.filter(email=customer_email).first()

            if user_obj and course_obj and paystack_ref:
                payment = Payment.objects.create(
                    user=user_obj,
                    course=course_obj,
                    amount=amount_paid,
                    reference=paystack_ref,
                    status='success',
                    paid_at=timezone.now(),
                    verified_at=timezone.now(),
                )
                logger.info("Created fallback payment record: %s", paystack_ref)
            else:
                logger.error(
                    "Cannot create fallback payment — missing data. "
                    "course_id=%s user_id=%s paystack_ref=%s",
                    course_id, user_id, paystack_ref
                )
                return None

        return payment

    @staticmethod
    def _enroll_user(user, course):
        user_profile, created_profile = UserProfile.objects.get_or_create(user=user)
        if created_profile:
            logger.info("Created new UserProfile for user: %s", user.username)

        if not user_profile.enrolled_courses.filter(id=course.id).exists():
            user_profile.enrolled_courses.add(course)
            logger.info("Enrolled user %s in course: %s", user.username, course.title)
            # Send enrollment confirmation email — try async first, fall back to sync
            try:
                from yoga_app.tasks import send_enrollment_confirmation_email
                send_enrollment_confirmation_email.delay(user.id, course.id)
            except Exception:
                # Redis/Celery unavailable — send synchronously so email still goes out
                try:
                    from yoga_app.tasks import send_enrollment_confirmation_email
                    send_enrollment_confirmation_email(user.id, course.id)
                except Exception as e:
                    logger.warning("Enrollment email failed for user %s: %s", user.username, e)
        else:
            logger.debug("User %s already enrolled in course: %s", user.username, course.title)

    @staticmethod
    def verify_webhook_signature(request_body: str, signature: str) -> bool:
        """Verify Paystack webhook HMAC-SHA512 signature."""
        if not signature or not settings.PAYSTACK_SECRET_KEY:
            return False

        secret_key = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
        computed_signature = hmac.new(
            secret_key,
            request_body.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature)
