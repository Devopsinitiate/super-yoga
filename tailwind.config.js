    /** @type {import('tailwindcss').Config} */
    module.exports = {
      // Configure Tailwind to scan your Django templates for classes
      content: [
        './yoga_app/templates/**/*.html',
        './yoga_app/static/js/**/*.js', // If you have JS files that dynamically add Tailwind classes
        './yoga_app/forms.py', // If you dynamically generate form classes in Python
      ],
      theme: {
        extend: {
          // You can extend Tailwind's default theme here
          // For example, custom colors, fonts, spacing, etc.
          colors: {
            // Define your custom amber shades if they are not standard Tailwind
            // 'amber-50': '#fffbeb',
            // 'amber-100': '#fef3c7',
            // 'amber-500': '#f59e0b',
            // 'amber-600': '#d97706',
            // 'amber-700': '#b45309',
          },
          fontFamily: {
            sans: ['Inter', 'sans-serif'], // Ensure Inter is the primary sans-serif font
          },
        },
      },
      plugins: [],
    }
    