import re

from typing import Dict, Any

from .abstract import MessageAnnotator

from flows import utils

log = utils.get_pylogger(__name__)


class RegexFirstOccurrenceExtractor(MessageAnnotator):
    def __init__(
        self, regex: str, key: str, assert_unique: bool, strip: bool, regex_fallback=None, verbose=True, **kwargs
    ):
        super().__init__(**kwargs)
        self.regex = regex
        self.regex_fallback = regex_fallback
        self.strip = strip
        self.key = key
        self.assert_unique = assert_unique
        self.verbose = verbose

    def __call__(self, message: str, **kwargs) -> Dict[str, Any]:
        txt = self._search(message, self.regex)

        if txt is None and self.regex_fallback:
            if isinstance(self.regex_fallback, str):
                self.regex_fallback = [self.regex_fallback]

            for fallback_regex in self.regex_fallback:
                txt = self._search(message, fallback_regex)
                if txt is not None:
                    if self.verbose:
                        log.info(f"Regex {self.regex} was not found, but {fallback_regex} was successful.")
                    break

        if txt is not None and self.strip:
            txt = txt.strip()

        return {self.key: txt}

    def _search(self, message, regex):
        match = re.search(regex, message)
        if match:
            if self.assert_unique:
                num_matches = len(match.groups())
                assert num_matches == 1, f"Regex {regex} expected to have only one group, found {num_matches}"
            return match.group(0)
        else:
            return None
