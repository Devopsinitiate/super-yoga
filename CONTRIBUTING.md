We welcome contributions to the Yoga Kailasa project! To ensure a smooth collaboration, please follow these guidelines.

### How to Contribute

1.  **Fork the Repository**: Start by forking the `yoga_kailasa_project` repository to your GitHub account.
2.  **Clone Your Fork**: Clone your forked repository to your local machine.
    ```bash
    git clone https://github.com/YOUR_USERNAME/yoga_kailasa_project.git
    cd yoga_kailasa_project
    ```
3.  **Create a New Branch**: For each new feature or bug fix, create a new branch. Use descriptive names (e.g., `feature/add-course-ratings`, `bugfix/fix-login-issue`).
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  **Make Your Changes**: Implement your feature or bug fix.
    -   Adhere to existing code style and conventions.
    -   Write clear, concise, and well-documented code.
    -   Ensure your code passes existing tests.
5.  **Write Tests**: If you're adding new features, please write unit and/or integration tests to cover your changes.
    ```bash
    python manage.py test
    ```
6.  **Update Documentation**: If your changes affect any functionality or setup, update the `README.md` or other relevant documentation files.
7.  **Commit Your Changes**: Write clear and concise commit messages.
    ```bash
    git commit -m "feat: Add new feature for X"
    ```
8.  **Push to Your Fork**: Push your new branch to your forked repository on GitHub.
    ```bash
    git push origin feature/your-feature-name
    ```
9.  **Create a Pull Request (PR)**:
    -   Go to the original `yoga_kailasa_project` repository on GitHub.
    -   You should see a prompt to create a new pull request from your recently pushed branch.
    -   Provide a clear title and detailed description of your changes.
    -   Reference any related issues.

### Code Style

-   Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
-   Adhere to existing Tailwind CSS and JavaScript conventions.

### Commit Message Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for our commit messages. This allows for easier tracking of changes and automated changelog generation.

The commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:

-   `feat`: A new feature
-   `fix`: A bug fix
-   `docs`: Documentation only changes
-   `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
-   `refactor`: A code change that neither fixes a bug nor adds a feature
-   `perf`: A code change that improves performance
-   `test`: Adding missing tests or correcting existing tests
-   `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
-   `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
-   `chore`: Other changes that don't modify src or test files
-   `revert`: Reverts a previous commit

### Reporting Bugs

If you find a bug, please open an issue on the GitHub repository. Provide a clear description of the bug, steps to reproduce it, and expected behavior.

### Feature Requests

Feel free to open an issue to suggest new features. Describe the feature, why it would be useful, and how it might be implemented.

Thank you for contributing to Yoga Kailasa!