<<<<<<< HEAD
# Yoga Kailasa

Yoga Kailasa is a Django-based web platform for online yoga courses, breathing techniques, and personalized consultations. It features user authentication, course management, testimonials, newsletter subscriptions, and more, all styled with Tailwind CSS for a modern, responsive UI.

## Features
- User registration, login, password reset, and profile management
- Browse and enroll in yoga courses
- Book private sessions with consultants
- Leave and read testimonials and course reviews
- Subscribe to a newsletter
- Responsive design with Tailwind CSS

## Setup
1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the server: `python manage.py runserver`

## Deployment
- Configure your production database and email settings in `settings.py`
- Collect static files: `python manage.py collectstatic`
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`

## License
MIT
>>>>>>> aaf18ed (Initial commit with all project files)
