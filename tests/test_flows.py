from src.flows.abstract import Flow
import pytest

def test_abstract_flow():
    flow = Flow("Abstract Flow", "Abstract Flow", [], [])

    # not implemented
    with pytest.raises(NotImplementedError):
        flow._flow()