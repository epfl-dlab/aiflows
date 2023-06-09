import os
import time

from src.flows import AtomicFlow
from src.messages import TaskMessage
from src.utils import caching_utils
from src.utils.caching_utils import flow_run_cache

SLEEP_TIME = 0.1

TMP_CACHE_DIR = os.path.abspath(os.path.join(os.getcwd(), '.tmp_flow_cache'))
caching_utils.CACHING_PARAMETERS.cache_dir = TMP_CACHE_DIR


class MyFlow(AtomicFlow):
    @flow_run_cache
    def run(self, input_data, expected_outputs):
        if self.dry_run:
            answer = 0
        else:
            answer = 0
            for k, v in input_data.items():
                answer += v

        time.sleep(SLEEP_TIME)

        return {self.expected_outputs[0]: answer}


my_flow = MyFlow(
    name="my-flow",
    description="flow-sum",
    expected_outputs=["sum"],
    expected_inputs=["v0", "v1"],
)

data = {"v0": 12, "v1": 23}
task_message = my_flow.package_task_message(
    recipient_flow=my_flow,
    task_name="task",
    task_data=data,
    expected_outputs=["sum"]
)

def _time_run(flow, message):
    t0 = time.time()
    answer = flow(message)
    time_taken = time.time() - t0
    return answer, time_taken


def test_no_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = False

    assert caching_utils.get_cache_dir() == TMP_CACHE_DIR

    _ = my_flow(task_message)
    assert not os.path.exists(TMP_CACHE_DIR)


def test_simple_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = True
    my_flow.run.clear_cache()

    answer_0, first_time = _time_run(my_flow, task_message)
    assert first_time > SLEEP_TIME

    answer_1, second_time = _time_run(my_flow, task_message)
    assert second_time < SLEEP_TIME

    assert answer_1.data == answer_0.data
    assert answer_1.data["sum"] == data["v0"] + data["v1"]


def test_flow_state_modification_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = True
    my_flow.run.clear_cache()

    answer_0, first_time = _time_run(my_flow, task_message)
    assert answer_0.data["sum"] == data["v0"] + data["v1"]
    assert first_time > SLEEP_TIME


    my_flow.dry_run = True
    answer_1, second_time = _time_run(my_flow, task_message)
    assert answer_1.data["sum"] == 0
    assert second_time > SLEEP_TIME


    answer_2, first_time = _time_run(my_flow, task_message)
    assert answer_2.data["sum"] == 0
    assert first_time < SLEEP_TIME

    new_flow = MyFlow.load_from_config(my_flow.flow_config)

    answer_3, first_time = _time_run(new_flow, task_message)
    assert answer_3.data["sum"] == data["v0"] + data["v1"]
    assert first_time < SLEEP_TIME

    new_flow.dry_run = True
    answer_4, first_time = _time_run(new_flow, task_message)
    assert answer_4.data["sum"] == 0
    assert first_time < SLEEP_TIME

    cache, _ = caching_utils.load_cache()
    assert len(cache) == 2


def test_task_message_modification_caching() -> None:
    pass


if __name__ == "__main__":
    test_flow_state_modification_caching()
