from flows.datasets.abstract import AbstractDataset
import os
import flows.utils as utils
import flows.utils.general_helpers


if __name__ == "__main__":
    log = utils.get_pylogger(__name__, stdout=True)
else:
    log = utils.get_pylogger(__name__)


class GenericDemonstrationsDataset(AbstractDataset):
    def __init__(self, data=None, **kwargs):
        super().__init__(kwargs)

        self.data = data

        if self.data is None:
            self._load_data()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    def _load_data(self):
        demonstrations_file = os.path.join(self.params["data_dir"], f"{self.params['demonstrations_id']}.jsonl")
        self.data = flows.utils.general_helpers.read_jsonlines(demonstrations_file)

        if self.params.get("ids_to_keep", False):
            if isinstance(self.params["ids_to_keep"], str):
                ids_to_keep = set(self.params["ids_to_keep"].split(","))
                ids_to_keep = [i.strip() for i in ids_to_keep]
            else:
                ids_to_keep = set(self.params["ids_to_keep"])

            ids_to_keep = [str(i) for i in ids_to_keep]
            self.data = [d for d in self.data if str(d["id"]) in ids_to_keep]

        log.info("Loaded the demonstrations for %d datapoints from %s", len(self.data), self.params["data_dir"])
