from jinja2 import Environment
from typing import List, Dict


class JinjaPrompt:
    r"""This class can be used to generate prompts from jinja templates

    :param \**kwargs:
        See below:
    :Keyword Arguments:
        * *input_variables* (``List[str]``) --
            A list of variables that are required to render the template
        * *partial_variables* (``Dict[str, Any]``) --
            A dictionary of variables and their values that are required to render the template (useful when one has some variables before others)
        * *template* (``str``) --
            The jinja template to render
    """

    def __init__(self, **kwargs):
        self.input_variables: set = set(kwargs.get("input_variables", []))
        self.partial_variables = kwargs.get("partial_variables", {})
        self.template: str = kwargs.get("template", "")
        self.environment = Environment()

    def format(self, **kwargs):
        r"""format the template with the given input variables

        :param \**kwargs: The input variables to render the template (should be a subset of the input variables)
        :return: The rendered template
        :rtype: str
        """
        template = self.environment.from_string(self.template)
        merged_args = {**self.partial_variables, **kwargs}
        return template.render(**merged_args)

    def partial(self, **kwargs):
        r"""Returns a new JinjaPrompt object, given some input variables (moves the given input variables from the input variables to the partial variables)
        This method is useful when one has some variables before others

        :param \**kwargs: The input variables to render the template (should be a subset of the input variables)
        :return: A new JinjaPrompt object
        :rtype: JinjaPrompt
        """

        new_partial_variables = {**self.partial_variables, **kwargs}
        new_input_variables = (self.input_variables ^ set(kwargs.keys())) & self.input_variables
        new_jinja_prompt_args = {
            "input_variables": new_input_variables,
            "partial_variables": new_partial_variables,
            "template": self.template,
        }

        return JinjaPrompt(**new_jinja_prompt_args)
