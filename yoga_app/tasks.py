from celery import shared_task
from django.core.mail import send_mail
import time

@shared_task
def send_newsletter_email(subject, message, recipient_list):
    send_mail(subject, message, 'no-reply@yogakailasa.com', recipient_list)

@shared_task
def send_booking_confirmation_email(user_email, booking_id):
    # Simulate a long-running operation
    time.sleep(2)
    send_mail(
        'Booking Confirmation',
        f'Your booking #{booking_id} is confirmed!',
        'no-reply@yogakailasa.com',
        [user_email]
    )

@shared_task
def generate_report_task(report_type, user_email):
    # Simulate report generation
    time.sleep(5)
    send_mail(
        'Your Report is Ready',
        f'The {report_type} report has been generated and is attached.',
        'no-reply@yogakailasa.com',
        [user_email]
    )
