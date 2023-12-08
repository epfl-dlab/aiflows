import re

from typing import Dict, Any

from aiflows.data_transformations.abstract import DataTransformation

from aiflows.utils import logging

log = logging.get_logger(__name__)


class RegexFirstOccurrenceExtractor(DataTransformation):
    """This class extracts the first occurrence of a regex from a given input key and saves it to the output key.

    :param regex: The regex to search for
    :type regex: str
    :param output_key: The output key to save the transformed data to
    :type output_key: str, optional
    :param assert_unique: Whether to assert that the regex has only one match
    :type assert_unique: bool, optional
    :param strip: Whether to strip the result
    :type strip: bool, optional
    :param input_key: The input key to apply the transformation to
    :type input_key: str
    :param regex_fallback: A regex to use if the first regex was not found
    :type regex_fallback: str, optional
    :param match_group: The match group to return
    :type match_group: int, optional
    """

    def __init__(
        self,
        regex: str,
        output_key: str,
        assert_unique: bool,
        strip: bool,
        input_key: str,
        regex_fallback: str = None,
        match_group: int = 0,
    ):
        super().__init__(output_key=output_key)
        self.input_key = input_key
        self.regex = regex
        self.regex_fallback = regex_fallback
        self.strip = strip
        self.assert_unique = assert_unique
        self.match_group = match_group

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Applies the transformation to the given data dictionary. It extracts the first occurrence of a regex from a given input key and saves it to the output key.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """

        txt = self._search(data_dict[self.input_key], self.regex)

        if txt is None and self.regex_fallback:
            if isinstance(self.regex_fallback, str):
                self.regex_fallback = [self.regex_fallback]

            for fallback_regex in self.regex_fallback:
                txt = self._search(data_dict[self.input_key], fallback_regex)
                if txt is not None:
                    log.info(f"Regex {self.regex} was not found, but {fallback_regex} was successful.")
                    break

        if txt is not None and self.strip:
            txt = txt.strip()

        data_dict[self.output_key] = txt
        return data_dict

    def _search(self, message, regex):
        """Searches for a regex in a message and returns the first match.

        :param message: The message to search in
        :type message: str
        :param regex: The regex to search for
        :type regex: str
        :return: The first match
        :rtype: str
        """
        match = re.search(regex, message)
        if match:
            if self.assert_unique:
                num_matches = len(match.groups())
                assert num_matches == 1, f"Regex {regex} expected to have only one group, found {num_matches}"
            return match.group(self.match_group)
        else:
            return None
