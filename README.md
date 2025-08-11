# Yoga Kailasa

Yoga Kailasa is a Django-based web platform for online yoga courses, breathing techniques, and personalized consultations. It features user authentication, course management, testimonials, newsletter subscriptions, and more, all styled with Tailwind CSS for a modern, responsive UI.

## Features
- User registration, login, password reset, and profile management
- Browse and enroll in yoga courses
- Book private sessions with consultants
- Leave and read testimonials and course reviews
- Subscribe to a newsletter
- Responsive design with Tailwind CSS
- **Automated testing with Django TestCase**
- **Continuous Integration (CI) using GitHub Actions**
- **Code coverage reporting with coverage.py**
- **Email notifications for CI test failures via Gmail SMTP**
- **Asynchronous tasks with Celery and Redis**
- **Secure payment integration with Paystack**
- **Rich text editing with CKEditor**
- **Enhanced security and password validation**
- **Performance optimizations (caching, optimized queries)**

## Setup
1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the server: `python manage.py runserver`

## Testing & CI
- Automated tests run on every push and pull request via GitHub Actions.
- Code coverage is reported using coverage.py.
- CI failures trigger email notifications (Gmail SMTP).
- To run tests locally: `python manage.py test`

## Asynchronous Tasks
- Celery is configured with Redis as the broker for background tasks (email, booking, reports).
- Start Celery worker: `celery -A yoga_kailasa worker -l info`

## Payment Integration
- Paystack is used for secure payment processing.
- Configure your Paystack keys in environment variables or `settings.py`.

## Deployment
- Configure your production database and email settings in `settings.py`
- Collect static files: `python manage.py collectstatic`
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`

## License
MIT

# Yoga Kailasa

Yoga Kailasa is a Django-based web platform for online yoga courses, breathing techniques, and personalized consultations. It features user authentication, course management, testimonials, newsletter subscriptions, and more, all styled with Tailwind CSS for a modern, responsive UI.

## Features
- User registration, login, password reset, and profile management
- Browse and enroll in yoga courses
- Book private sessions with consultants
- Leave and read testimonials and course reviews
- Subscribe to a newsletter
- Responsive design with Tailwind CSS
- **Automated testing with Django TestCase**
- **Continuous Integration (CI) using GitHub Actions**
- **Code coverage reporting with coverage.py**
- **Email notifications for CI test failures via Gmail SMTP**
- **Asynchronous tasks with Celery and Redis**
- **Secure payment integration with Paystack**
- **Rich text editing with CKEditor**
- **Enhanced security and password validation**
- **Performance optimizations (caching, optimized queries)**

## Setup
1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the server: `python manage.py runserver`

## Testing & CI
- Automated tests run on every push and pull request via GitHub Actions.
- Code coverage is reported using coverage.py.
- CI failures trigger email notifications (Gmail SMTP).
- To run tests locally: `python manage.py test`

## Asynchronous Tasks
- Celery is configured with Redis as the broker for background tasks (email, booking, reports).
- Start Celery worker: `celery -A yoga_kailasa worker -l info`

## Payment Integration
- Paystack is used for secure payment processing.
- Configure your Paystack keys in environment variables or `settings.py`.

## Deployment
- Configure your production database and email settings in `settings.py`
- Collect static files: `python manage.py collectstatic`
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`

## License
MIT
