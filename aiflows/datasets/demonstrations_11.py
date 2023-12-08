import jinja2

from .abstract import AbstractDataset

import os
from aiflows.utils import logging
import aiflows.utils.general_helpers as general_helpers


if __name__ == "__main__":
    log = logging.get_logger(__name__, stdout=True)
else:
    log = logging.get_logger(__name__)


class GenericDemonstrationsDataset(AbstractDataset):
    def __init__(self, data=None, **kwargs):
        super().__init__(kwargs)

        self.data = data

        self.io_example_formatter = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(
            self.params["io_example_template"]
        )
        self.explanation_formatter = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(
            self.params["explanation_template"]
        )

        if self.data is None:
            self._load_data()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        dp = self.data[idx]

        io_examples = []

        idx = 1
        for x, y in dp["public_tests_io"]:
            _input = "\n".join(x)
            kwargs = {"idx": idx, "input": _input, "output": y}
            io_examples.append(self.io_example_formatter.render(**kwargs))
            idx += 1

        formatted_io_examples = self.params["io_example_separator"].join(io_examples)

        if dp["note"] is None:
            dp["io_examples_and_explanation"] = formatted_io_examples
        else:
            formatted_note = self.explanation_formatter.render(note=dp["note"])
            dp["io_examples_and_explanation"] = "\n\n".join([formatted_io_examples, formatted_note])

        dp["formatted_tags"] = ", ".join(dp["tags"])
        # dp["formatted_tags"] = "-" + "\n-".join(dp["tags"])  # alternative

        return dp

    def _load_data(self):
        demonstrations_file = os.path.join(self.params["data_dir"], f"{self.params['demonstrations_id']}.jsonl")
        self.data = general_helpers.read_jsonlines(demonstrations_file)

        if self.params.get("ids_to_keep", False):
            if isinstance(self.params["ids_to_keep"], str):
                ids_to_keep = set(self.params["ids_to_keep"].split(","))
            else:
                ids_to_keep = set(self.params["ids_to_keep"])

            self.data = [d for d in self.data if d["id"] in ids_to_keep]

        log.info("Loaded the demonstrations for %d datapoints from %s", len(self.data), self.params["data_dir"])
