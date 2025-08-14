# Yoga Kailasa

Yoga Kailasa is a Django-based web platform for online yoga courses, breathing techniques, and personalized consultations. It features user authentication, course management, testimonials, newsletter subscriptions, and more, all styled with Tailwind CSS for a modern, responsive UI.

## Key Features

-   **User Management**: Complete user authentication system with registration, login, password reset, and profile management.
-   **Course Management**: Browse, enroll, and track progress in a variety of yoga courses.
-   **Personalized Consultations**: Book one-on-one sessions with experienced yoga consultants.
-   **Community & Feedback**: Leave testimonials, course reviews, and engage in discussions.
-   **Content Discovery**:
    -   **Global Search**: Find poses, techniques, courses, and blog posts with live search suggestions.
    -   **Categorization & Tagging**: Filter content with a robust tagging and category system.
-   **Payments & Subscriptions**:
    -   **Secure Payments**: Integrated with Paystack for reliable payment processing.
    -   **Newsletter**: Keep users engaged with a Mailchimp-integrated newsletter.
-   **User Engagement**:
    -   **Notifications**: Real-time alerts for important events and interactions.
    -   **User Dashboard**: A personalized dashboard to track progress, bookings, and notifications.
-   **Content & SEO**:
    -   **Blog**: A feature-rich blog with categories, tags, and social sharing.
    -   **SEO Best Practices**: Implemented for improved visibility in search engines.

## Recent Improvements

-   **CI/CD Enhancements**:
    -   The GitHub Actions workflow for Django CI/CD has been updated for better reliability.
    -   Added code coverage reporting with `coverage.py`.
    -   Integrated email notifications for CI test failures.
-   **Asynchronous Task Processing**:
    -   Implemented Celery with Redis for handling background tasks like sending emails and processing bookings, improving application performance and user experience.
-   **Enhanced User Experience**:
    -   **Request a Report**: Users can now request detailed reports, which are generated asynchronously.
    -   **Improved Notifications**: A more robust notification system keeps users informed of key events.
-   **Code Quality & Maintainability**:
    -   **Refactored Models**: Updated and improved the database models for better organization and efficiency.
    -   **Comprehensive Tests**: Added a significant number of new tests to ensure application stability.
    -   **Validators**: Implemented custom validators to ensure data integrity.

## Setup

1.  Clone the repository.
2.  Create a virtual environment and activate it.
3.  Install dependencies: `pip install -r requirements.txt`
4.  Apply migrations: `python manage.py migrate`
5.  Create a superuser: `python manage.py createsuperuser`
6.  Run the development server: `python manage.py runserver`

## Testing & CI

-   Automated tests run on every push and pull request via GitHub Actions.
-   To run tests locally: `python manage.py test`

## Asynchronous Tasks

-   Celery is configured with Redis as the broker.
-   To start the Celery worker: `celery -A yoga_kailasa worker -l info`

## Payment Integration

-   Paystack is used for secure payment processing.
-   Configure your Paystack keys in your environment variables or `settings.py`.

## Deployment

Deploy the project using a WSGI server like Gunicorn and a reverse proxy like Nginx. Ensure that you have set up your environment variables for production.

## Contribution Guidelines

We welcome contributions! Please see `CONTRIBUTING.md` for more details on how to get involved.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.