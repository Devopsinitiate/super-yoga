# yoga_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Avg, Count, Case, When, Value, BooleanField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import requests
import json
from django.utils import timezone
import hmac
import hashlib
import uuid
from django.db import IntegrityError, transaction
from django.urls import reverse
from datetime import timedelta # NEW: Import timedelta for date calculations

from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm # Keep this import for the base form if needed elsewhere
from django.contrib.auth.views import LoginView, LogoutView

from django_ratelimit.decorators import ratelimit # Import ratelimit decorator
from django.utils.decorators import method_decorator # NEW: Import method_decorator

from django.views.decorators.cache import cache_page # NEW: Import cache_page decorator

from django.views.decorators.cache import never_cache # Import never_cache
from .tasks import send_newsletter_email, send_booking_confirmation_email, generate_report_task # NEW: Import the Celery tasks

from .models import (
    YogaPose,
    BreathingTechnique,
    Course,
    Consultant,
    Testimonial,
    Booking,
    NewsletterSubscription,
    ContactMessage,
    Payment,
    UserProfile,
    UserCourseCompletion,
    CourseReview,
    Module,
    Lesson,
    UserLessonCompletion,
    DiscussionTopic,
    DiscussionPost,
    Notification,
    LessonComment,
    BlogPostCategory, # NEW: Import Blog models
    BlogPost,         # NEW: Import Blog models
    BlogComment,      # NEW: Import Blog models
    Tag               # NEW: Import the Tag model
)

from .forms import (
    BookingForm,
    TestimonialForm,
    NewsletterSubscriptionForm,
    ContactMessageForm,
    UserRegisterForm,
    UserLoginForm,
    UserAccountUpdateForm,
    UserProfileForm,
    CourseReviewForm,
    DiscussionTopicForm,
    DiscussionPostForm,
    LessonCommentForm,
    CustomPasswordChangeForm, # NEW: Import the custom password change form
    BlogCommentForm # NEW: Import BlogCommentForm
)

# Custom LoginView with success message
@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')

class CustomLoginView(LoginView):
    # The @ratelimit decorator is now correctly applied to the 'dispatch' method
    # using method_decorator, ensuring it receives the HttpRequest object.
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.username}! You have logged in successfully.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Custom LogoutView with success message
class CustomLogoutView(LogoutView):
    @method_decorator(never_cache) # Apply never_cache decorator
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have logged out successfully.")
        response = super().dispatch(request, *args, **kwargs)
        # Explicitly set headers to prevent caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

def home_view(request):
    """
    Renders the homepage, fetching data from various models to populate sections.
    Optimized with prefetch_related/select_related for efficient data retrieval.
    This view's output is now conditionally cached.
    """
    # If there are messages, do not cache this response to ensure messages are consumed.
    if messages.get_messages(request):
        yoga_poses = YogaPose.objects.all().order_by('?')[:3]
        breathing_techniques = BreathingTechnique.objects.all().order_by('name')
        
        courses = Course.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by('-is_popular', 'price')
        
        consultants = Consultant.objects.all().order_by('name')
        testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')[:3] # Filter for approved testimonials

        contact_form = ContactMessageForm()

        context = {
            'yoga_poses': yoga_poses,
            'breathing_techniques': breathing_techniques,
            'courses': courses,
            'consultants': consultants,
            'testimonials': testimonials,
            'contact_form': contact_form,
        }
        response = render(request, 'yoga_app/index.html', context)
        return response

    # Otherwise, cache the page for 5 minutes
    @cache_page(60 * 5)
    def _home_view_cached(request):
        yoga_poses = YogaPose.objects.all().order_by('?')[:3]
        breathing_techniques = BreathingTechnique.objects.all().order_by('name')
        
        courses = Course.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by('-is_popular', 'price')
        
        consultants = Consultant.objects.all().order_by('name')
        testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')[:3] # Filter for approved testimonials

        contact_form = ContactMessageForm()

        context = {
            'yoga_poses': yoga_poses,
            'breathing_techniques': breathing_techniques,
            'courses': courses,
            'consultants': consultants,
            'testimonials': testimonials,
            'contact_form': contact_form,
        }
        return render(request, 'yoga_app/index.html', context)

    return _home_view_cached(request)

@ratelimit(key='ip', rate='5/m', block=True) # Apply rate limiting to registration
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully for {user.username}! Welcome to Yoga Kailasa.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below to register.")
            print(f"Register Form Errors: {form.errors}")
    else:
        form = UserRegisterForm()

    context = {
        'form': form
    }
    return render(request, 'yoga_app/registration/register.html', context)

def booking_view(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            if request.user.is_authenticated:
                booking.user = request.user
            booking.save()
            # Trigger async booking confirmation email
            send_booking_confirmation_email.delay(booking.user.email if booking.user else booking.email, booking.id)
            messages.success(request, 'Your booking request has been submitted successfully! We will contact you shortly.')
            return redirect('booking')
        else:
            messages.error(request, 'There was an error with your booking. Please correct the errors below.')
    else:
        form = BookingForm()
    
    # Fetch consultants to display on the booking page if needed
    consultants = Consultant.objects.filter(is_available=True).order_by('name')

    context = {
        'form': form,
        'consultants': consultants,
    }
    # RENDER NEW DEDICATED TEMPLATE
    return render(request, 'yoga_app/booking_page.html', context)

@ratelimit(key='ip', rate='3/m', block=True) # Apply rate limiting to feedback submission
def feedback_view(request):
    """
    Handles submission of the testimonial/feedback form.
    Now renders a dedicated feedback.html page instead of redirecting to home.
    """
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your valuable feedback! It will be reviewed shortly.')
            print("DEBUG: Testimonial submitted successfully.")
            return redirect('feedback') # Redirect to the same dedicated feedback page
        else:
            messages.error(request, 'There was an error submitting your feedback. Please ensure all required fields are filled.')
            print(f"DEBUG: Testimonial Form Errors: {form.errors}")
    else:
        form = TestimonialForm()
    
    # Fetch approved testimonials to display on the feedback page
    approved_testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')

    context = {
        'form': form,
        'testimonials': approved_testimonials,
    }
    return render(request, 'yoga_app/feedback.html', context) # Render the dedicated feedback.html

from django.views.decorators.csrf import csrf_exempt # Add this import

def newsletter_subscribe_view(request):
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            form.save()
            # Trigger async newsletter email (example usage)
            send_newsletter_email.delay(
                'Welcome to Yoga Kailasa Newsletter!',
                'Thank you for subscribing to our newsletter.',
                [email]
            )
            messages.success(request, 'Thank you for subscribing to our newsletter!')
            return redirect('home')
        else: # form.is_valid() is False
            # Check for specific unique email error
            if 'email' in form.errors and any('already exists' in e for e in form.errors['email']):
                messages.info(request, 'You are already subscribed to our newsletter!')
            else:
                messages.error(request, 'Please enter a valid email address to subscribe.')
                print(f"Newsletter Form Errors: {form.errors}")
            return redirect('home')
    return redirect('home')

def pose_list_view(request):
    poses_list = YogaPose.objects.all().order_by('name')

    query = request.GET.get('q')
    if query:
        poses_list = poses_list.filter(
            Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
        ).distinct()

    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        poses_list = poses_list.filter(difficulty=difficulty_filter)

    paginator = Paginator(poses_list, 9)
    page = request.GET.get('page')
    try:
        yoga_poses = paginator.page(page)
    except PageNotAnInteger:
        yoga_poses = paginator.page(1)
    except EmptyPage:
        yoga_poses = paginator.page(paginator.num_pages)

    context = {
        'yoga_poses': yoga_poses,
        'query': query,
        'difficulty_filter': difficulty_filter,
        'difficulty_choices': YogaPose.DIFFICULTY_CHOICES,
    }
    return render(request, 'yoga_app/pose_list.html', context)

def pose_detail_view(request, pose_id):
    """
    Displays details of a single yoga pose.
    """
    pose = get_object_or_404(YogaPose, id=pose_id)
    context = {
        'pose': pose,
    }
    return render(request, 'yoga_app/pose_detail.html', context)


def breathing_list_view(request):
    techniques_list = BreathingTechnique.objects.all().order_by('name')

    query = request.GET.get('q')
    if query:
        techniques_list = techniques_list.filter(
            Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
        ).distinct()

    paginator = Paginator(techniques_list, 6)
    page = request.GET.get('page')
    try:
        breathing_techniques = paginator.page(page)
    except PageNotAnInteger:
        breathing_techniques = paginator.page(1)
    except EmptyPage:
        breathing_techniques = paginator.page(paginator.num_pages)

    context = {
        'breathing_techniques': breathing_techniques,
        'query': query,
    }
    return render(request, 'yoga_app/breathing_list.html', context)

def breathing_technique_detail_view(request, technique_id):
    """
    Displays details of a single breathing technique.
    """
    technique = get_object_or_404(BreathingTechnique, id=technique_id)
    context = {
        'technique': technique,
    }
    return render(request, 'yoga_app/breathing_technique_detail.html', context)


def course_list_view(request):
    """
    Displays a list of courses with advanced filtering and sorting options.
    Optimized queries for filtering, sorting, and fetching filter options.
    """
    courses_list = Course.objects.all().prefetch_related('reviews')

    query = request.GET.get('q')
    if query:
        courses_list = courses_list.filter(
            Q(title__icontains=query) | 
            Q(instructor_name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()

    price_filter = request.GET.get('price_filter')
    if price_filter == 'free':
        courses_list = courses_list.filter(price=0.00)
    elif price_filter == 'paid':
        courses_list = courses_list.exclude(price=0.00)

    instructor_filter = request.GET.get('instructor_filter')
    if instructor_filter:
        courses_list = courses_list.filter(instructor_name__icontains=instructor_filter)

    duration_filter = request.GET.get('duration_filter')
    if duration_filter:
        courses_list = courses_list.filter(duration__icontains=duration_filter)

    min_rating_filter = request.GET.get('min_rating_filter')
    if min_rating_filter:
        try:
            min_rating_filter = float(min_rating_filter)
            courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating')).filter(
                Q(avg_rating__gte=min_rating_filter) | Q(avg_rating__isnull=True, avg_rating__gte=0)
            )
        except ValueError:
            pass

    sort_by = request.GET.get('sort_by', 'popular_desc')
    
    if sort_by == 'rating_desc' and 'avg_rating' not in courses_list.query.annotations:
        courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating'))

    if sort_by == 'newest':
        courses_list = courses_list.order_by('-created_at')
    elif sort_by == 'price_asc':
        courses_list = courses_list.order_by('price')
    elif sort_by == 'price_desc':
        courses_list = courses_list.order_by('-price')
    elif sort_by == 'alpha_asc':
        courses_list = courses_list.order_by('title')
    elif sort_by == 'rating_desc':
        courses_list = courses_list.order_by('-avg_rating') 
    else:
        courses_list = courses_list.order_by('-is_popular', 'title')


    paginator = Paginator(courses_list, 9)
    page = request.GET.get('page')
    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
        courses = paginator.page(paginator.num_pages)

    all_instructors = Course.objects.values_list('instructor_name', flat=True).distinct().order_by('instructor_name')
    all_durations = Course.objects.values_list('duration', flat=True).distinct().order_by('duration')


    context = {
        'courses': courses,
        'query': query,
        'price_filter': price_filter,
        'instructor_filter': instructor_filter,
        'duration_filter': duration_filter,
        'min_rating_filter': min_rating_filter,
        'sort_by': sort_by,
        'all_instructors': all_instructors,
        'all_durations': all_durations,
    }
    return render(request, 'yoga_app/course_list.html', context)

def initiate_payment_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to purchase courses.")
            return redirect('login')

        user_email = request.user.email
        if not user_email:
            user_email = f"{request.user.username}@example.com"
            messages.warning(request, "Your account does not have an email. Using a placeholder for payment. Please update your profile.")

        amount_kobo = int(course.price * 100)
        transaction_reference = str(uuid.uuid4())

        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                course=course,
                amount=course.price,
                status='pending',
                reference=transaction_reference,
            )

        print(f"--- Paystack Initiation Debug ---")
        print(f"Course ID: {course_id}")
        print(f"Course Title: {course.title}")
        print(f"Amount (NGN Kobo): {amount_kobo}")
        print(f"Customer Email (from Django view): {user_email}")
        print(f"Paystack Public Key (from settings): {settings.PAYSTACK_PUBLIC_KEY}")
        print(f"User ID (if authenticated): {request.user.id if request.user.is_authenticated else 'N/A'}")
        print(f"Generated Transaction Reference: {transaction_reference}")
        print(f"---------------------------------")

        paystack_metadata = {
            'course_id': course.id,
            'payment_id': payment.id,
            'our_reference': transaction_reference,
            'user_id': request.user.id,
        }
        
        context = {
            'course': course,
            'amount': amount_kobo,
            'email': user_email,
            'public_key': settings.PAYSTACK_PUBLIC_KEY,
            'metadata_json': json.dumps(paystack_metadata),
            'transaction_reference': transaction_reference,
        }
        return render(request, 'yoga_app/payment_initiate.html', context)
    else:
        messages.error(request, 'Invalid request method for payment initiation.')
        return redirect('home')

def verify_payment_view(request):
    """
    View to verify payment callback from gateway (typically a browser GET redirect).
    This provides immediate user feedback but webhooks are the authoritative source.
    """
    if request.method == 'GET':
        reference = request.GET.get('reference')
        if not reference:
            messages.error(request, "Payment verification failed: No transaction reference provided.")
            return redirect('home')

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        verification_url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"

        try:
            response = requests.get(verification_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data['status'] and data['data']['status'] == 'success':
                messages.success(request, f"Payment successful! Your enrollment is being processed.")
                return redirect('dashboard')
            else:
                gateway_response = data['data'].get('gateway_response', 'No specific response.')
                messages.error(request, f"Payment failed: {gateway_response}. Please try again.")
                print(f"Paystack verification failed for {reference} via GET: {data.get('message', 'No message')}, Gateway Response - {gateway_response}")
                return redirect('home')

        except requests.exceptions.RequestException as e:
            messages.error(request, "Could not verify payment due to a network error. Please contact support.")
            print(f"Paystack API request failed during GET verification: {e}")
            return redirect('home')
        except json.JSONDecodeError:
            messages.error(request, "Invalid response from payment gateway. Please contact support.")
            print(f"Failed to decode JSON from Paystack during GET verification: {response.text}")
            return redirect('home')
        except Exception as e:
            messages.error(request, "An unexpected error occurred during payment verification. Please contact support.")
            print(f"An unexpected error occurred during GET verification: {e}")
            return redirect('home')
    else:
        messages.error(request, 'Invalid request for payment verification.')
        return redirect('home')

@csrf_exempt
def paystack_webhook_view(request):
    """
    Handles Paystack webhook notifications for payment status updates.
    This is the authoritative source for updating payment status and enrolling users.
    Ensures idempotency and robust error handling.
    """
    print("DEBUG: Webhook view accessed.")

    if request.method == 'POST':
        paystack_signature = request.headers.get('x-paystack-signature')
        if not paystack_signature:
            print("Webhook Error: No X-Paystack-Signature header found.")
            return JsonResponse({'status': 'error', 'message': 'Signature missing'}, status=400)

        request_body = request.body.decode('utf-8')
        secret_key = settings.PAYSTACK_SECRET_KEY.encode('utf-8')

        computed_signature = hmac.new(
            key=secret_key,
            msg=request_body.encode('utf-8'),
            digestmod=hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(computed_signature, paystack_signature):
            print(f"Webhook Security Error: Invalid signature. Computed: {computed_signature}, Received: {paystack_signature}")
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        try:
            event_data = json.loads(request_body)
            event_type = event_data.get('event')
            transaction_data = event_data.get('data')

            print(f"--- Paystack Webhook Received: {event_type} ---")
            print(f"Transaction Data: {json.dumps(transaction_data, indent=2)}")

            if event_type == 'charge.success' and transaction_data:
                paystack_reference = transaction_data.get('reference')
                status = transaction_data.get('status')
                amount_paid = transaction_data.get('amount') / 100
                customer_email = transaction_data.get('customer', {}).get('email')
                metadata = transaction_data.get('metadata', {})
                
                course_id_from_meta = metadata.get('course_id')
                user_id_from_meta = metadata.get('user_id')
                our_generated_reference_from_meta = metadata.get('our_reference')

                print(f"Webhook Success: Paystack Ref={paystack_reference}, Status={status}, Amount={amount_paid}, Email={customer_email}, Course ID (meta)={course_id_from_meta}, User ID (meta)={user_id_from_meta}, Our Ref (meta)={our_generated_reference_from_meta}")

                if status == 'success':
                    try:
                        with transaction.atomic():
                            payment = None
                            if our_generated_reference_from_meta:
                                payment = Payment.objects.filter(reference=our_generated_reference_from_meta).first()
                                if payment:
                                    print(f"DEBUG: Found Payment record using 'our_reference' from metadata: {our_generated_reference_from_meta}")
                            
                            if not payment and paystack_reference:
                                payment = Payment.objects.filter(reference=paystack_reference).first()
                                if payment:
                                    print(f"DEBUG: Found Payment record using Paystack's reference: {paystack_reference}")

                            if not payment:
                                print(f"DEBUG: No existing Payment record found. Attempting to create new one as fallback.")
                                course_obj = Course.objects.filter(id=course_id_from_meta).first()
                                user_obj = User.objects.filter(id=user_id_from_meta).first()
                                if not user_obj and customer_email:
                                    user_obj = User.objects.filter(email=customer_email).first()

                                if user_obj and course_obj and paystack_reference:
                                    payment = Payment.objects.create(
                                        user=user_obj,
                                        course=course_obj,
                                        amount=amount_paid,
                                        reference=paystack_reference,
                                        status='success',
                                        paid_at=timezone.now(),
                                        verified_at=timezone.now(),
                                    )
                                    print(f"DEBUG: New payment record created from webhook for reference {paystack_reference}.")
                                else:
                                    print(f"ERROR: Cannot create new payment record from webhook fallback: Missing user ({user_obj}), course ({course_obj}), or Paystack reference ({paystack_reference}).")
                                    return JsonResponse({'status': 'error', 'message': 'Missing data for fallback payment creation'}, status=400)

                            if payment and payment.status != 'success':
                                payment.status = 'success'
                                payment.paid_at = timezone.now()
                                payment.verified_at = timezone.now()
                                payment.save(update_fields=['status', 'paid_at', 'verified_at', 'updated_at'])
                                print(f"DEBUG: Payment record for {payment.reference} (ID: {payment.id}) updated to 'success'.")
                            elif payment and payment.status == 'success':
                                print(f"DEBUG: Payment record for {payment.reference} (ID: {payment.id}) already 'success'. Idempotent operation.")
                            
                            if payment and payment.user and payment.course:
                                user_profile, created_profile = UserProfile.objects.get_or_create(user=payment.user)
                                if created_profile:
                                    print(f"DEBUG: Created new UserProfile for {payment.user.username}.")

                                if not user_profile.enrolled_courses.filter(id=payment.course.id).exists():
                                    user_profile.enrolled_courses.add(payment.course)
                                    print(f"DEBUG: User {payment.user.username} successfully enrolled in course {payment.course.title}.")
                                else:
                                    print(f"DEBUG: User {payment.user.username} was already enrolled in course {payment.course.title}.")
                            else:
                                print(f"WARNING: Cannot enroll user/course for payment {payment.reference}: User ({payment.user}) or Course ({payment.course}) not linked.")

                    except Exception as e:
                        print(f"ERROR: Webhook processing failed for reference {paystack_reference}: {e}")
                        return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)

                return JsonResponse({'status': 'success'})
            else:
                print(f"Webhook: Received non-success 'charge.success' event or missing transaction data for reference {transaction_data.get('reference')}: {status}")
                return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            print("Webhook Error: Invalid JSON payload.")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Webhook Error: Unexpected error processing event: {e}")
            return JsonResponse({'status': 'error', 'message': 'Internal Server Error'}, status=500)
    else:
        print("Webhook Error: Non-POST request to webhook endpoint.")
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def user_dashboard_view(request):
    """
    Displays the courses the logged-in user is enrolled in and their payment history.
    Optimized to calculate progress efficiently and fetch notifications.
    """
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        print(f"DEBUG: Created UserProfile for {user.username} during dashboard access.")
        
    enrolled_courses = user_profile.enrolled_courses.all().prefetch_related(
        'modules__lessons',
        'user_completions',
        'modules__lessons__userlessoncompletion_set'
    ).annotate(
        total_lessons_count=Count('modules__lessons', distinct=True)
    )

    courses_data = []
    for course in enrolled_courses:
        completed_lessons_count = UserLessonCompletion.objects.filter(
            user=user,
            lesson__module__course=course
        ).count()
        
        progress_percentage = 0
        if course.total_lessons_count > 0:
            progress_percentage = int((completed_lessons_count / course.total_lessons_count) * 100)
        
        is_completed = UserCourseCompletion.objects.filter(user=user, course=course).exists()

        courses_data.append({
            'course': course,
            'is_completed': is_completed,
            'total_lessons': course.total_lessons_count,
            'completed_lessons_count': completed_lessons_count,
            'progress_percentage': progress_percentage,
        })

    # Calculate the total number of courses completed by the user
    completed_courses_count = UserCourseCompletion.objects.filter(user=user).count()

    payment_history = Payment.objects.filter(user=user).select_related('course').order_by('-paid_at')

    last_viewed_lesson = user_profile.last_viewed_lesson
    if last_viewed_lesson:
        last_viewed_lesson = Lesson.objects.filter(id=last_viewed_lesson.id).select_related('module__course').first()

    recent_notifications = Notification.objects.filter(recipient=user).select_related('sender').order_by('-created_at')[:5]

    context = {
        'enrolled_courses_data': courses_data,
        'user_profile': user_profile,
        'payment_history': payment_history,
        'last_viewed_lesson': last_viewed_lesson,
        'recent_notifications': recent_notifications,
        'completed_courses_count': completed_courses_count, # <--- Add this to context
    }
    return render(request, 'yoga_app/user_dashboard.html', context)


def course_detail_view(request, course_id):
    """
    Displays details of a single course, showing full content if the user is enrolled,
    otherwise showing a preview and an option to enroll.
    Also handles displaying existing reviews and the review submission form.
    Optimized queries for enrollment, completion, and reviews.
    """
    course = get_object_or_404(Course.objects.prefetch_related('reviews'), id=course_id)
    
    is_enrolled = False
    is_completed = False
    review_form = None
    user_review = None
    
    if request.user.is_authenticated:
        user = request.user
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            print(f"DEBUG: Created UserProfile for {user.username} during course detail access.")
        
        is_enrolled = user_profile.enrolled_courses.filter(id=course.id).exists()
        
        if is_enrolled:
            is_completed = UserCourseCompletion.objects.filter(user=user, course=course).exists()
            
            user_review = CourseReview.objects.filter(course=course, user=user).first()
            
            if user_review:
                review_form = CourseReviewForm(instance=user_review)
            else:
                review_form = CourseReviewForm()

    reviews = CourseReview.objects.filter(course=course).select_related('user').order_by('-submitted_at')
    
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    total_reviews_count = reviews.count()

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'is_completed': is_completed,
        'review_form': review_form,
        'user_review': user_review,
        'reviews': reviews,
        'average_rating': average_rating,
        'total_reviews_count': total_reviews_count,
    }
    return render(request, 'yoga_app/course_detail.html', context)

@login_required
def course_content_view(request, course_id, lesson_id=None):
    """
    Displays the structured content (modules and lessons) of a course for enrolled users.
    Allows navigation between lessons and displays the current lesson's content.
    Updates the user's last_viewed_lesson in their UserProfile.
    Adds logic for next/previous lesson navigation and lesson comments.
    Optimized queries for lessons, completions, and comments.
    """
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    user_profile = get_object_or_404(UserProfile, user=user)

    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You are not enrolled in '{course.title}'. Please enroll to access the full content.")
        return redirect('course_detail', course_id=course.id)

    all_lessons_in_course = Lesson.objects.filter(module__course=course).select_related('module').order_by('module__order', 'order')

    current_lesson = None
    if lesson_id:
        current_lesson = get_object_or_404(all_lessons_in_course, id=lesson_id)
    else:
        if user_profile.last_viewed_lesson and user_profile.last_viewed_lesson.module.course == course:
            current_lesson = user_profile.last_viewed_lesson
        elif all_lessons_in_course.exists():
            current_lesson = all_lessons_in_course.first()

    comment_form = None
    if current_lesson:
        if request.method == 'POST':
            comment_form = LessonCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.lesson = current_lesson
                comment.user = user
                comment.save()
                messages.success(request, "Your comment has been added successfully!")
                return redirect('course_content', course_id=course_id, lesson_id=current_lesson.id)
            else:
                messages.error(request, "There was an error adding your comment. Please correct the highlighted fields.")
                print(f"Lesson Comment Form Errors: {comment_form.errors}")
        else:
            comment_form = LessonCommentForm()

    lesson_comments = []
    if current_lesson:
        lesson_comments = LessonComment.objects.filter(lesson=current_lesson).select_related('user').order_by('created_at')

    if current_lesson:
        if user_profile.last_viewed_lesson != current_lesson:
            user_profile.last_viewed_lesson = current_lesson
            user_profile.save(update_fields=['last_viewed_lesson'])
            print(f"DEBUG: User {user.username} last viewed lesson updated to: {current_lesson.title}")

    previous_lesson = None
    next_lesson = None
    if current_lesson:
        lessons_list = list(all_lessons_in_course)
        try:
            current_lesson_index = -1
            for i, lesson in enumerate(lessons_list):
                if lesson.id == current_lesson.id:
                    current_lesson_index = i
                    break

            if current_lesson_index != -1:
                if current_lesson_index > 0:
                    previous_lesson = lessons_list[current_lesson_index - 1]
                if current_lesson_index < len(lessons_list) - 1:
                    next_lesson = lessons_list[current_lesson_index + 1]
        except Exception as e:
            print(f"WARNING: Error determining next/previous lesson: {e}")


    completed_lesson_ids = set(UserLessonCompletion.objects.filter(
        user=user,
        lesson__module__course=course
    ).values_list('lesson__id', flat=True))

    total_lessons = all_lessons_in_course.count()
    completed_lessons_count = len(completed_lesson_ids)
    
    progress_percentage = 0
    if total_lessons > 0:
        progress_percentage = int((completed_lessons_count / total_lessons) * 100)

    course_is_completed_by_user = UserCourseCompletion.objects.filter(user=user, course=course).exists()

    modules = Module.objects.filter(course=course).prefetch_related('lessons').order_by('order')


    context = {
        'course': course,
        'modules': modules,
        'current_lesson': current_lesson,
        'completed_lesson_ids': completed_lesson_ids,
        'total_lessons': total_lessons,
        'completed_lessons_count': completed_lessons_count,
        'progress_percentage': progress_percentage,
        'course_is_completed_by_user': course_is_completed_by_user,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'comment_form': comment_form,
        'lesson_comments': lesson_comments,
    }
    return render(request, 'yoga_app/course_content.html', context)


def enroll_free_course_view(request, course_id):
    """
    Handles enrollment for free courses directly, without Paystack.
    Creates a Payment record with 0 amount and enrolls the user.
    Uses transaction.atomic for data consistency.
    """
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)

        if not course.is_free:
            messages.error(request, "This course is not free. Please use the payment gateway to enroll.")
            return redirect('course_detail', course_id=course.id)

        if not request.user.is_authenticated:
            messages.error(request, "Please log in to enroll in courses.")
            return redirect('login')

        user_profile, created_profile = UserProfile.objects.get_or_create(user=request.user)
        if created_profile:
            print(f"DEBUG: Created UserProfile for {request.user.username} during free course enrollment.")

        if user_profile.enrolled_courses.filter(id=course.id).exists():
            messages.info(request, f"You are already enrolled in '{course.title}'.")
            return redirect('dashboard') 

        try:
            with transaction.atomic():
                free_payment_reference = f"FREE-{course.id}-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
                
                Payment.objects.create(
                    user=request.user,
                    course=course,
                    amount=0.00,
                    reference=free_payment_reference,
                    status='success', 
                    paid_at=timezone.now(),
                    verified_at=timezone.now(),
                )
                print(f"DEBUG: Created free payment record for user {request.user.username} for course {course.title}.")

                user_profile.enrolled_courses.add(course)
                messages.success(request, f"You have successfully enrolled in '{course.title}'!")
                print(f"DEBUG: User {request.user.username} successfully enrolled in free course {course.title}.")
                return redirect('dashboard')

        except IntegrityError as e:
            messages.info(request, f"You are already enrolled in '{course.title}'.")
            print(f"DEBUG: IntegrityError during free course enrollment (likely duplicate payment ref): {e}")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during enrollment: {e}")
            print(f"ERROR: Free course enrollment failed for user {request.user.username}, course {course.title}: {e}")
            return redirect('course_detail', course_id=course.id)
    else:
        messages.error(request, "Invalid request for free course enrollment.")
        return redirect('home')

@login_required 
def mark_course_complete_view(request, course_id):
    """
    Handles marking a course as complete for the logged-in user.
    Ensures all lessons are completed before marking the course complete.
    Uses transaction.atomic for data consistency.
    """
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course.id).exists():
            messages.error(request, f"You are not enrolled in '{course.title}'. Cannot mark as complete.")
            return redirect('course_detail', course_id=course.id)

        if UserCourseCompletion.objects.filter(user=user, course=course).exists():
            messages.info(request, f"You have already marked '{course.title}' as complete.")
            print(f"DEBUG: User {user.username} attempted to mark course {course.title} as complete, but it was already complete.")
            return redirect('course_detail', course_id=course.id)

        try:
            with transaction.atomic():
                total_lessons = Lesson.objects.filter(module__course=course).count()
                completed_lessons_count = UserLessonCompletion.objects.filter(
                    user=user,
                    lesson__module__course=course
                ).count()

                if total_lessons > 0 and completed_lessons_count < total_lessons:
                    messages.error(request, f"Please complete all lessons ({completed_lessons_count}/{total_lessons}) in '{course.title}' before marking the course as complete.")
                    return redirect('course_content_base', course_id=course.id)

                UserCourseCompletion.objects.create(user=user, course=course)
                messages.success(request, f"Congratulations! You have completed '{course.title}'!")
                print(f"DEBUG: User {user.username} marked course {course.title} as complete.")
        except IntegrityError:
            messages.info(request, f"This course is already marked as complete for you.")
            print(f"DEBUG: IntegrityError (duplicate entry) when marking course {course.title} complete for user {user.username}.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred while marking '{course.title}' as complete: {e}")
            print(f"ERROR: Failed to mark course {course.title} as complete for user {user.username}: {e}")
        
        return redirect('course_detail', course_id=course_id)
    else:
        messages.error(request, "Invalid request to mark course complete.")
        return redirect('home')

from django.contrib.auth import update_session_auth_hash, get_user_model # Import get_user_model

@login_required
def profile_update_view(request):
    """
    Allows a logged-in user to update their username and email address, and change their password.
    Also handles updating profile picture and bio.
    Uses transaction.atomic for data consistency across multiple forms.
    """
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if created:
        print(f"DEBUG: Created UserProfile for {request.user.username} during profile update view access.")

    if request.method == 'POST':
        user_account_form = UserAccountUpdateForm(request.POST, instance=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST) # NEW: Use CustomPasswordChangeForm

        with transaction.atomic():
            profile_updated = False
            password_updated = False
            user_profile_updated = False

            if 'update_account' in request.POST:
                if user_account_form.is_valid():
                    user_account_form.save()
                    messages.success(request, 'Your account (username and email) has been updated successfully!')
                    profile_updated = True
                else:
                    messages.error(request, 'Error updating account. Please check the form.')
                    print(f"User Account Update Errors: {user_account_form.errors}")

            if 'update_profile' in request.POST:
                if user_profile_form.is_valid():
                    user_profile_form.save()
                    # After saving UserProfile, refresh the user object in the session
                    # to reflect changes immediately in the navbar/other templates
                    request.user = get_user_model().objects.get(pk=request.user.pk)
                    messages.success(request, 'Your profile picture and bio have been updated successfully!')
                    user_profile_updated = True
                else:
                    messages.error(request, 'Error updating profile. Please check the form.')
                    print(f"User Profile Form Errors: {user_profile_form.errors}")

            if 'change_password' in request.POST:
                if password_form.is_valid():
                    user = password_form.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Your password has been changed successfully!')
                    password_updated = True
                else:
                    messages.error(request, 'Error changing password. Please check the form.')
                    print(f"Password Change Errors: {password_form.errors}")
            
            if profile_updated or password_updated or user_profile_updated:
                return redirect('profile_edit')
        
    else: # GET request
        user_account_form = UserAccountUpdateForm(instance=request.user)
        user_profile_form = UserProfileForm(instance=user_profile)
        password_form = CustomPasswordChangeForm(user=request.user) # NEW: Use CustomPasswordChangeForm

    context = {
        'user_account_form': user_account_form,
        'user_profile_form': user_profile_form,
        'password_form': password_form,
        'user_profile': user_profile,
    }
    return render(request, 'yoga_app/profile_edit.html', context)

@ratelimit(key='ip', rate='3/m', block=True) # Apply rate limiting to contact form
def contact_view(request):
    """
    Handles displaying and processing the contact message form.
    """
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'There was an error sending your message. Please correct the highlighted fields.')
            print(f"Contact Form Errors: {form.errors}")
    else:
        form = ContactMessageForm()

    context = {
        'form': form,
    }
    return render(request, 'yoga_app/contact.html', context)

def global_search_view(request):
    """
    Handles global search across Yoga Poses, Breathing Techniques, and Courses.
    Optimized with distinct filters and ordering.
    """
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    pose_difficulty_filter = request.GET.get('pose_difficulty', '')
    course_price_filter = request.GET.get('course_price', '')

    yoga_poses = YogaPose.objects.none()
    breathing_techniques = BreathingTechnique.objects.none()
    courses = Course.objects.none()

    if query:
        if not category_filter or category_filter == 'poses':
            yoga_poses = YogaPose.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
            ).distinct()
        
        if not category_filter or category_filter == 'breathing':
            breathing_techniques = BreathingTechnique.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
            ).distinct()
        
        if not category_filter or category_filter == 'courses':
            courses = courses.filter(
                Q(title__icontains=query) | Q(instructor_name__icontains=query) | Q(description__icontains=query)
            ).distinct()
    else:
        if not category_filter or category_filter == 'poses':
            yoga_poses = YogaPose.objects.all()
        if not category_filter or category_filter == 'breathing':
            breathing_techniques = BreathingTechnique.objects.all()
        if not category_filter or category_filter == 'courses':
            courses = Course.objects.all()


    if pose_difficulty_filter and (not category_filter or category_filter == 'poses'):
        yoga_poses = yoga_poses.filter(difficulty=pose_difficulty_filter)

    if course_price_filter and (not category_filter or category_filter == 'courses'):
        if course_price_filter == 'free':
            courses = courses.filter(price=0.00)
        elif course_price_filter == 'paid':
            courses = courses.exclude(price=0.00)

    yoga_poses = yoga_poses.order_by('name')
    breathing_techniques = breathing_techniques.order_by('name')
    courses = courses.order_by('-is_popular', 'title')

    context = {
        'query': query,
        'category_filter': category_filter,
        'pose_difficulty_filter': pose_difficulty_filter,
        'course_price_filter': course_price_filter,
        'yoga_poses': yoga_poses,
        'breathing_techniques': breathing_techniques,
        'courses': courses,
        'difficulty_choices': YogaPose.DIFFICULTY_CHOICES,
    }
    return render(request, 'yoga_app/search_results.html', context)

def global_search_suggestions_api(request):
    query = request.GET.get('q', '')
    suggestions = []

    if query:
        # Search Yoga Poses
        poses = YogaPose.objects.filter(
            Q(name__icontains=query) | Q(sanskrit_name__icontains=query)
        ).values('id', 'name')[:5] # Limit to 5 suggestions

        for pose in poses:
            suggestions.append({
                'type': 'pose',
                'title': pose['name'],
                'url': reverse('pose_detail', args=[pose['id']])
            })

        # Search Breathing Techniques
        techniques = BreathingTechnique.objects.filter(
            Q(name__icontains=query) | Q(sanskrit_name__icontains=query)
        ).values('id', 'name')[:5] # Limit to 5 suggestions

        for tech in techniques:
            suggestions.append({
                'type': 'breathing',
                'title': tech['name'],
                'url': reverse('breathing_technique_detail', args=[tech['id']])
            })

        # Search Courses
        courses = Course.objects.filter(
            Q(title__icontains=query) | Q(instructor_name__icontains=query)
        ).values('id', 'title')[:5] # Limit to 5 suggestions

        for course in courses:
            suggestions.append({
                'type': 'course',
                'title': course['title'],
                'url': reverse('course_detail', args=[course['id']])
            })
            
        # Search Blog Posts
        blog_posts = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query)
        ).values('slug', 'title')[:5] # Limit to 5 suggestions

        for blog_post in blog_posts:
            suggestions.append({
                'type': 'blog_post',
                'title': blog_post['title'],
                'url': reverse('blog_detail', args=[blog_post['slug']])
            })

    return JsonResponse({'suggestions': suggestions})

def about_view(request):
    """
    Renders the About Us page.
    """
    return render(request, 'yoga_app/about.html')

@login_required
def delete_account_view(request):
    """
    Allows a logged-in user to delete their own account.
    Requires POST request for security.
    Uses transaction.atomic for data consistency.
    """
    if request.method == 'POST':
        user = request.user
        with transaction.atomic():
            logout(request)
            user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')
    else:
        messages.error(request, 'Invalid request to delete account.')
        return redirect('dashboard')

@login_required
def submit_course_review_view(request, course_id):
    """
    Handles submission or update of a course review.
    Optimized to fetch existing review efficiently.
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, "You must be enrolled in this course to submit or edit a review.")
        return redirect('course_detail', course_id=course.id)

    existing_review = CourseReview.objects.filter(course=course, user=user).first()

    if request.method == 'POST':
        if existing_review:
            form = CourseReviewForm(request.POST, instance=existing_review)
        else:
            form = CourseReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.user = user
            review.save()
            messages.success(request, 'Your review has been submitted/updated successfully!')
            return redirect('course_detail', course_id=course_id)
        else:
            print(f"DEBUG: Course Review form errors: {form.errors}")
            messages.error(request, 'There was an error submitting/updating your review. Please correct the highlighted fields.')
            
            is_enrolled = True
            is_completed = UserCourseCompletion.objects.filter(user=user, course=course).exists()
            reviews = CourseReview.objects.filter(course=course).select_related('user').order_by('-submitted_at')
            average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            total_reviews_count = reviews.count()

            context = {
                'course': course,
                'is_enrolled': is_enrolled,
                'is_completed': is_completed,
                'review_form': form,
                'user_review': existing_review,
                'reviews': reviews,
                'average_rating': average_rating,
                'total_reviews_count': total_reviews_count,
            }
            return render(request, 'yoga_app/course_detail.html', context)
    else:
        messages.error(request, 'Invalid request method for submitting/editing a review.')
        return redirect('course_detail', course_id=course_id)


@login_required
def mark_lesson_complete_view(request, course_id, lesson_id):
    """
    Handles marking a specific lesson as complete for the logged-in user.
    Uses transaction.atomic for data consistency.
    """
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            messages.error(request, f"You are not enrolled in '{lesson.module.course.title}'. Cannot mark lesson as complete.")
            return redirect('course_detail', course_id=course.id)

        if UserLessonCompletion.objects.filter(user=user, lesson=lesson).exists():
            messages.info(request, f"Lesson '{lesson.title}' is already marked as complete.")
            print(f"DEBUG: Lesson {lesson.title} already complete for user {user.username}.")
            return redirect('course_content', course_id=course_id, lesson_id=lesson_id)

        try:
            with transaction.atomic():
                UserLessonCompletion.objects.create(user=user, lesson=lesson)
                messages.success(request, f"Lesson '{lesson.title}' marked as complete!")
                print(f"DEBUG: User {user.username} marked lesson {lesson.title} as complete.")
        except IntegrityError:
            messages.info(request, f"Lesson '{lesson.title}' is already marked as complete.")
            print(f"DEBUG: IntegrityError (duplicate entry) when marking lesson {lesson.title} complete for user {user.username}.")
        except Exception as e:
            messages.error(request, f"An error occurred while marking '{lesson.title}' as complete: {e}")
            print(f"ERROR: Failed to mark lesson {lesson.title} as complete for user {user.username}: {e}")
        
        return redirect('course_content', course_id=course_id, lesson_id=lesson_id)
    else:
        messages.error(request, "Invalid request to mark lesson complete.")
        return redirect('course_content_base', course_id=course_id)


@login_required
@ratelimit(key='ip', rate='5/m', block=True) # Apply rate limiting to discussion topic creation
def course_discussion_list_view(request, course_id):
    """
    Displays a list of discussion topics for a course and allows creation of new topics.
    Optimized to prefetch user for topics.
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to access its discussion forum.")
        return redirect('course_detail', course_id=course.id)

    topics = DiscussionTopic.objects.filter(course=course).select_related('user').order_by('-created_at')

    if request.method == 'POST':
        form = DiscussionTopicForm(request.POST, course=course)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.course = course
            topic.user = user
            topic.save()
            messages.success(request, f"Discussion topic '{topic.title}' created successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error creating your discussion topic. Please correct the highlighted fields.")
            print(f"Discussion Topic Form Errors: {form.errors}")
    else:
        form = DiscussionTopicForm(course=course)

    context = {
        'course': course,
        'topics': topics,
        'form': form,
    }
    return render(request, 'yoga_app/course_discussion_list.html', context)


@login_required
@ratelimit(key='ip', rate='10/m', block=True) # Apply rate limiting to discussion post creation
def discussion_topic_detail_view(request, course_id, topic_id):
    """
    Displays a single discussion topic and its posts.
    Optimized to prefetch related users for topic and posts.
    """
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic.objects.select_related('user'), id=topic_id, course=course)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to access this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    posts = topic.posts.all().select_related('user').order_by('created_at')

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.user = user
            post.save()

            if topic.user != user:
                Notification.objects.create(
                    recipient=topic.user,
                    sender=user,
                    notification_type='reply',
                    message=f"{user.username} replied to your topic: '{topic.title}'",
                    link=reverse('course_discussion_detail', args=[course.id, topic.id])
                )
            
            if post.parent_post and post.parent_post.user != user:
                Notification.objects.create(
                    recipient=post.parent_post.user,
                    sender=user,
                    notification_type='reply',
                    message=f"{user.username} replied to your post in topic: '{topic.title}'",
                    link=reverse('course_discussion_detail', args=[course.id, topic.id])
                )

            messages.success(request, "Your reply has been added!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error adding your reply. Please correct the highlighted fields.")
            print(f"Discussion Post Form Errors: {form.errors}")
    else:
        form = DiscussionPostForm()

    context = {
        'course': course,
        'topic': topic,
        'posts': posts,
        'form': form,
    }
    return render(request, 'yoga_app/discussion_topic_detail.html', context)


@login_required
def edit_discussion_topic_view(request, course_id, topic_id):
    """
    Allows the user to edit their own discussion topic.
    """
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    user = request.user

    if topic.user != user:
        messages.error(request, "You do not have permission to edit this discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to edit this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = DiscussionTopicForm(request.POST, instance=topic, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Discussion topic updated successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error updating your discussion topic. Please correct the highlighted fields.")
            print(f"Edit Discussion Topic Form Errors: {form.errors}")
    else:
        form = DiscussionTopicForm(instance=topic, course=course)

    context = {
        'course': course,
        'topic': topic,
        'form': form,
        'is_editing': True,
    }
    return render(request, 'yoga_app/discussion_topic_edit.html', context)


@login_required
def delete_discussion_topic_view(request, course_id, topic_id):
    """
    Allows the user to delete their own discussion topic.
    Uses transaction.atomic for data consistency.
    """
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    user = request.user

    if topic.user != user:
        messages.error(request, "You do not have permission to delete this discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to delete this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        with transaction.atomic():
            topic.delete()
        messages.success(request, f"Discussion topic '{topic.title}' deleted successfully.")
        return redirect('course_discussion_list', course_id=course.id)
    else:
        messages.error(request, "Invalid request method for deleting a discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)


@login_required
def edit_discussion_post_view(request, course_id, topic_id, post_id):
    """
    Allows the user to edit their own discussion post.
    """
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    post = get_object_or_404(DiscussionPost, id=post_id, topic=topic)
    user = request.user

    if post.user != user:
        messages.error(request, "You do not have permission to edit this discussion post.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to edit this discussion post.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Discussion post updated successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error updating your discussion post. Please correct the highlighted fields.")
            print(f"Edit Discussion Post Form Errors: {form.errors}")
    else:
        form = DiscussionPostForm(instance=post)

    context = {
        'course': course,
        'topic': topic,
        'post': post,
        'form': form,
        'is_editing': True,
    }
    return render(request, 'yoga_app/discussion_post_edit.html', context)


@login_required
def delete_discussion_post_view(request, course_id, topic_id, post_id):
    """
    Allows the user to delete their own discussion post.
    Uses transaction.atomic for data consistency.
    """
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    post = get_object_or_404(DiscussionPost, id=post_id, topic=topic)
    user = request.user

    if post.user != user:
        messages.error(request, "You do not have permission to delete this discussion post.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to delete this discussion post.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        with transaction.atomic():
            post.delete()
        messages.success(request, "Discussion post deleted successfully.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
    else:
        messages.error(request, "Invalid request method for deleting a discussion post.")
        return redirect('course_discussion_detail', course_id=course_id, topic_id=topic.id)


@login_required
@csrf_exempt
def toggle_topic_like(request, course_id, topic_id):
    """
    Toggles a like on a discussion topic.
    Expects an AJAX POST request.
    Optimized to prefetch user for notification.
    """
    if request.method == 'POST':
        topic = get_object_or_404(DiscussionTopic, id=topic_id, course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Not enrolled in course'}, status=403)

        liked = False
        with transaction.atomic():
            if user in topic.likes.all():
                topic.likes.remove(user)
                liked = False
            else:
                topic.likes.add(user)
                liked = True
                if topic.user != user:
                    Notification.objects.create(
                        recipient=topic.user,
                        sender=user,
                        notification_type='reply',
                        message=f"{user.username} liked your topic: '{topic.title}'",
                        link=reverse('course_discussion_detail', args=[course_id, topic.id])
                    )
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': topic.likes.count()
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
@csrf_exempt
def toggle_post_like(request, course_id, topic_id, post_id):
    """
    Toggles a like on a discussion post.
    Expects an AJAX POST request.
    Optimized to prefetch user for notification.
    """
    if request.method == 'POST':
        post = get_object_or_404(DiscussionPost, id=post_id, topic__id=topic_id, topic__course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Not enrolled in course'}, status=403)

        liked = False
        with transaction.atomic():
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
                if post.user != user:
                    Notification.objects.create(
                        recipient=post.user,
                        sender=user,
                        notification_type='reply',
                        message=f"{user.username} liked your post in topic: '{post.topic.title}'",
                        link=reverse('course_discussion_detail', args=[course_id, topic_id])
                    )
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': post.likes.count()
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
def get_notifications_api(request):
    """
    Fetches notifications for the current user (unread first, then recent read).
    Marks unread notifications as read when fetched.
    Returns a JSON response.
    Optimized with select_related for sender.
    """
    notifications_qs = Notification.objects.filter(recipient=request.user).select_related('sender').order_by('read', '-created_at')
    
    unread_notifications = notifications_qs.filter(read=False)
    recent_read_notifications = notifications_qs.filter(read=True)[:5]

    notifications_data = []

    for notif in unread_notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'message': notif.message,
            'link': notif.link,
            'read': notif.read,
            'created_at': notif.created_at.strftime("%b %d, %Y %I:%M %p"),
            'sender_username': notif.sender.username if notif.sender else None
        })
    
    for notif in recent_read_notifications:
        if notif.id not in [d['id'] for d in notifications_data]:
            notifications_data.append({
                'id': notif.id,
                'type': notif.notification_type,
                'message': notif.message,
                'link': notif.link,
                'read': notif.read,
                'created_at': notif.created_at.strftime("%b %d, %Y %I:%M %p"),
                'sender_username': notif.sender.username if notif.sender else None
            })

    if unread_notifications.exists():
        with transaction.atomic():
            unread_notifications.update(read=True)
            print(f"DEBUG: Marked {unread_notifications.count()} notifications as read for {request.user.username}.")

    return JsonResponse({'notifications': notifications_data})

@login_required
@csrf_exempt
def mark_notification_read_view(request, notification_id):
    """
    Marks a specific notification as read.
    Expects an AJAX POST request.
    """
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
            if not notification.read:
                with transaction.atomic():
                    notification.read = True
                    notification.save(update_fields=['read', 'updated_at'])
                return JsonResponse({'status': 'success', 'message': 'Notification marked as read.'})
            else:
                return JsonResponse({'status': 'success', 'message': 'Notification already read.'})
        except Exception as e:
            print(f"ERROR: Failed to mark notification {notification_id} as read: {e}")
            return JsonResponse({'status': 'error', 'message': 'Failed to mark notification as read.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def all_notifications_view(request):
    """
    Displays all notifications for the current user on a dedicated page.
    Notifications are ordered by creation date, with unread ones first.
    Marks all unread notifications as read when the page is viewed.
    Optimized with select_related for sender.
    """
    notifications = Notification.objects.filter(recipient=request.user).select_related('sender').order_by('read', '-created_at')
    
    unread_on_page_load = notifications.filter(read=False)
    if unread_on_page_load.exists():
        with transaction.atomic():
            unread_on_page_load.update(read=True)
            print(f"DEBUG: Marked {unread_on_page_load.count()} notifications as read on all_notifications_view for {request.user.username}.")

    context = {
        'notifications': notifications,
    }
    return render(request, 'yoga_app/all_notifications.html', context)


# NEW: Blog Views

def blog_list_view(request): 
    """
    Displays a list of blog posts, with optional filtering by category, tag, author, date range, and search functionality.
    """
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')
    categories = BlogPostCategory.objects.all().order_by('name')
    tags = Tag.objects.all().order_by('name')
    
    current_category = None
    current_tag = None
    current_author = None # NEW
    date_range_filter = None # NEW
    sort_by = request.GET.get('sort_by', 'newest') # NEW: Default sort by newest

    query = request.GET.get('q')
    category_slug = request.GET.get('category_slug')
    tag_slug = request.GET.get('tag_slug')
    author_id = request.GET.get('author_id') # NEW: Get author ID
    date_range = request.GET.get('date_range') # NEW: Get date range filter

    if category_slug:
        current_category = get_object_or_404(BlogPostCategory, slug=category_slug)
        posts = posts.filter(category=current_category)

    if tag_slug:
        current_tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=current_tag)

    if author_id: # NEW: Filter by author
        try:
            current_author = get_object_or_404(User, id=author_id)
            posts = posts.filter(author=current_author)
        except ValueError:
            pass # Invalid author_id, ignore filter

    if date_range: # NEW: Filter by date range
        date_range_filter = date_range
        today = timezone.now().date()
        if date_range == 'past_week':
            posts = posts.filter(published_date__gte=today - timedelta(days=7))
        elif date_range == 'past_month':
            posts = posts.filter(published_date__gte=today - timedelta(days=30))
        elif date_range == 'past_year':
            posts = posts.filter(published_date__gte=today - timedelta(days=365))
        # Add more date range options if needed

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(author__username__icontains=query)
        ).distinct()

    # Apply sorting
    if sort_by == 'oldest':
        posts = posts.order_by('published_date')
    elif sort_by == 'title_asc':
        posts = posts.order_by('title')
    elif sort_by == 'title_desc':
        posts = posts.order_by('-title')
    elif sort_by == 'most_liked': # NEW: Sort by most liked
        posts = posts.annotate(likes_count=Count('likes')).order_by('-likes_count', '-published_date')
    else: # Default to newest
        posts = posts.order_by('-published_date')


    # Fetch all authors who have published posts for the author filter dropdown
    all_authors = User.objects.filter(blog_posts__isnull=False).distinct().order_by('username')


    # Fetch recent posts for the sidebar (still needed for the sidebar, distinct from related posts)
    recent_posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')[:5]

    # Pagination
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    
    try:
        posts_page = paginator.page(page_number)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)

    context = {
        'posts': posts_page,
        'categories': categories,
        'tags': tags,
        'current_category': current_category,
        'current_tag': current_tag,
        'query': query,
        'recent_posts': recent_posts,
        'all_authors': all_authors, # NEW: Pass all authors for filter dropdown
        'current_author': current_author, # NEW: Pass current author for pre-selection
        'date_range_filter': date_range_filter, # NEW: Pass current date range for pre-selection
        'sort_by': sort_by, # NEW: Pass current sort_by for pre-selection
    }
    return render(request, 'yoga_app/blog_list.html', context)

def blog_detail_view(request, post_slug):
    """
    Displays a single blog post and its comments.
    Also passes information about likes and whether the current user has liked the post.
    Includes logic to fetch related posts.
    """
    post = get_object_or_404(BlogPost.objects.select_related('author').prefetch_related('comments__user', 'tags', 'likes', 'category'), slug=post_slug, is_published=True)
    comments = post.comments.all().order_by('created_at')
    comment_form = BlogCommentForm()

    is_liked_by_user = False
    if request.user.is_authenticated:
        is_liked_by_user = post.likes.filter(id=request.user.id).exists()

    # --- Logic for Related Posts ---
    related_posts = BlogPost.objects.filter(is_published=True).exclude(id=post.id)

    # Prioritize by shared tags
    if post.tags.exists():
        # Get IDs of tags associated with the current post
        current_post_tag_ids = list(post.tags.values_list('id', flat=True))
        
        # Filter related posts that share any of these tags
        related_posts = related_posts.filter(tags__in=current_post_tag_ids).distinct()
        
        # Annotate with the count of shared tags for ordering
        related_posts = related_posts.annotate(
            shared_tags_count=Count('tags', filter=Q(tags__in=current_post_tag_ids))
        ).order_by('-shared_tags_count', '-published_date')
    
    # If not enough related posts by tags, or no tags, try by category
    if related_posts.count() < 4 and post.category: # Aim for up to 4 related posts
        category_related_posts = BlogPost.objects.filter(
            is_published=True, 
            category=post.category
        ).exclude(id=post.id).order_by('-published_date')
        
        # Combine and remove duplicates, ensuring tag-matched posts are still prioritized
        # Convert to list to combine and slice
        combined_related_posts = list(related_posts)
        seen_ids = set([p.id for p in combined_related_posts]) # Add existing related post IDs to seen_ids
        
        for p in category_related_posts:
            if p.id not in seen_ids:
                combined_related_posts.append(p)
                seen_ids.add(p.id)
        related_posts = combined_related_posts
    
    # Ensure we only get a maximum of 4 related posts
    related_posts = related_posts[:4]
    # --- End Logic for Related Posts ---


    # Fetch recent posts for the sidebar (still needed for the sidebar, distinct from related posts)
    recent_posts = BlogPost.objects.filter(is_published=True).exclude(slug=post_slug).order_by('-published_date')[:5]

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'recent_posts': recent_posts,
        'is_liked_by_user': is_liked_by_user,
        'likes_count': post.likes.count(),
        'related_posts': related_posts, # NEW: Pass related posts to the template
    }
    return render(request, 'yoga_app/blog_detail.html', context)

@login_required
@ratelimit(key='ip', rate='5/m', block=True) # Apply rate limiting to blog comment submission
def add_blog_comment_view(request, post_slug):
    """
    Handles submission of new comments for a blog post.
    """
    post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
    if request.method == 'POST':
        form = BlogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')

            # Create notification for blog post author
            if post.author and post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='blog_comment',
                    message=f'"{request.user.username}" commented on your blog post: "{post.title}".',
                    link=reverse('blog_detail', args=[post.slug])
                )
            return redirect('blog_detail', post_slug=post.slug)
        else:
            messages.error(request, 'There was an error adding your comment. Please correct the errors.')
    return redirect('blog_detail', post_slug=post_slug)

@login_required
@csrf_exempt
def toggle_blog_post_like(request, post_slug):
    """
    Toggles a like on a blog post.
    Expects an AJAX POST request.
    """
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
        user = request.user

        liked = False
        with transaction.atomic():
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
                # Create notification for blog post author if different from the liker
                if post.author and post.author != user:
                    Notification.objects.create(
                        recipient=post.author,
                        sender=user,
                        notification_type='blog_post_like', # Use the new notification type
                        message=f'"{user.username}" liked your blog post: "{post.title}".',
                        link=reverse('blog_detail', args=[post.slug])
                    )
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': post.likes.count()
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# --- Consultant Views (NEW) ---
def consultant_list_view(request):
    """
    Displays a list of all available consultants.
    """
    consultants = Consultant.objects.filter(is_available=True).order_by('name')
    context = {
        'consultants': consultants,
    }
    return render(request, 'yoga_app/consultant_list.html', context)

def consultant_detail_view(request, consultant_id):
    """
    Displays detailed information about a single consultant.
    """
    consultant = get_object_or_404(Consultant, pk=consultant_id)
    context = {
        'consultant': consultant,
    }
    return render(request, 'yoga_app/consultant_detail.html', context)

@login_required
def request_report_view(request):
    """
    Allows a logged-in user to request a report (e.g., progress, payment, or activity report).
    Triggers the async report generation Celery task and notifies the user.
    """
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'progress')
        user_email = request.user.email
        if user_email:
            generate_report_task.delay(report_type, user_email)
            messages.success(request, f"Your {report_type} report is being generated and will be sent to {user_email}.")
        else:
            messages.error(request, "No email address found for your account. Please update your profile.")
        return redirect('dashboard')
    return render(request, 'yoga_app/request_report.html')
