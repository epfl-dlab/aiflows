.. _coding_standards:

Coding Standards
================

When contributing to aiFlows library, it's essential to adhere to the following coding standards to maintain consistency, readability, and the overall quality of the codebase:

1. Simplicity and Readability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Strive to make your code as simple and readable as possible. Use clear and meaningful variable/function names, and avoid unnecessary complexity.

2. Best Practices
^^^^^^^^^^^^^^^^^^^^^^

Follow industry best practices when implementing features or fixing bugs. This includes adhering to language-specific conventions and guidelines.

3. Documentation
^^^^^^^^^^^^^^^^^^^^^^^^

Document your code thoroughly. Provide comments where necessary to explain complex logic or algorithms. Use clear and concise language to describe your thought process.

4. Docstrings in Sphinx Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For all new functions and classes, include docstrings in Sphinx format. These docstrings should describe the purpose, parameters, return values, and possibly exceptions raised by the function or class. Here is an example of the docstring of a function in the Sphinx format::

   def example_function(param1, param2):
       """
       Brief description of the function.

       :param param1: Description of the first parameter.
       :param param2: Description of the second parameter.
       :return: Description of the return value.
       :raises CustomException: Description of when this exception is raised.
       """
       # Function implementation
       return result

For more details on the Sphinx docstring format check out this link: `Sphinx Docstring Format`_.

5. Backward Compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that your code changes are backward compatible whenever possible. This helps maintain the stability of the library for existing users.

6. Thorough Testing
^^^^^^^^^^^^^^^^^^^^

Create comprehensive tests for your code. Tests should cover various scenarios, including edge cases, to ensure the robustness of your implementation.

7. Test Coverage
^^^^^^^^^^^^^^^^

Try to maintain or increase test coverage when adding new features or modifying existing ones when needed. Aim for a high percentage of code coverage to catch potential issues early.

8. Feature Tests
^^^^^^^^^^^^^^^^

When introducing new features, include corresponding tests. Every feature should have a test, and existing tests should be updated as needed.


---------------

Your dedication to simplicity, readability, and best practices is greatly appreciated. Your contributions help make the aiFlows library more accessible, robust, and user-friendly for the entire community.

Once again, thank you for being a valued member of our community and for your commitment to making aiFlows even better. Happy coding! 🚀⭐


.. _Sphinx Docstring Format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html