from flows.message_annotators.abstract import MessageAnnotator

from flows import utils

log = utils.get_pylogger(__name__)


class EndOfInteraction(MessageAnnotator):
    def __init__(self, end_of_interaction_message: str, key: str, verbose: bool, **kwargs):
        super().__init__(**kwargs)
        self.eoi_message = end_of_interaction_message
        self.key = key
        self.verbose = verbose

    def __call__(self, message: str, **kwargs):
        is_in = self.eoi_message.lower() in message.lower()

        if self.verbose and is_in:
            log.info(f"End of interaction detected!")

        return {self.key: is_in}
