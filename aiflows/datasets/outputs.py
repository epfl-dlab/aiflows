from aiflows.utils import logging
from aiflows.datasets import AbstractDataset
from aiflows.utils.general_helpers import read_outputs

log = logging.get_logger(__name__)


class OutputsDataset(AbstractDataset):
    def __init__(self, data=None, **kwargs):
        super().__init__(kwargs)

        self.data = data
        self.filter_failed = kwargs.get("filter_failed", True)

        if self.data is None:
            self._load_data()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # See the models.api_model._get_outputs_to_write() function for the data that is available for each datapoint
        return self.data[idx]

    def _load_data(self):
        self.data = read_outputs(self.params["data_dir"])

        if self.filter_failed:
            log.info("[Output DS] Filtering out the datapoints for which the prediction failed")
            self.data = [sample for sample in self.data if sample["error"] is None]

        if len(self.data) == 0:
            log.warning("[Output DS] No predictions were loaded from %s", self.params["data_dir"])
        else:
            log.info(
                "[Output DS] Loaded the predictions for %d datapoints from %s", len(self.data), self.params["data_dir"]
            )

    @staticmethod
    def get_output_data(sample_data, idx=None):
        if idx is None:
            output_data = []
            for inference_output in sample_data["inference_outputs"]:
                output_data.append(inference_output["data"]["output_data"])
        else:
            output_data = sample_data["inference_outputs"][idx]["data"]["output_data"]

        return output_data
