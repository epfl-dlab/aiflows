import pytest
from flows.datasets import AbstractDataset, GenericDemonstrationsDataset
import flows.utils.general_helpers


def test_abstract_dataset():
    dataset = AbstractDataset(params={})
    with pytest.raises(NotImplementedError):
        len(dataset)
    with pytest.raises(NotImplementedError):
        dataset[0]
    with pytest.raises(NotImplementedError):
        dataset._load_data()


def test_generic_demonstrations(monkeypatch):
    monkeypatch.setattr(flows.utils.general_helpers, "read_jsonlines", lambda x: [{"id": 1}, {"id": 2}])

    dataset = GenericDemonstrationsDataset(
        data=None, data_dir="data/demonstrations", demonstrations_id="high_level_reasoning", ids_to_keep=None
    )
    assert len(dataset) == 2
    assert dataset[0]["id"] == 1

    dataset = GenericDemonstrationsDataset(
        data=None, data_dir="data/demonstrations", demonstrations_id="high_level_reasoning", ids_to_keep=[1]
    )
    assert len(dataset) == 1

    dataset = GenericDemonstrationsDataset(
        data=None, data_dir="data/demonstrations", demonstrations_id="high_level_reasoning", ids_to_keep="1,2"
    )
    assert len(dataset) == 2

    dataset = GenericDemonstrationsDataset(
        data=None, data_dir="data/demonstrations", demonstrations_id="high_level_reasoning", ids_to_keep="1,, 2"
    )
    assert len(dataset) == 2
