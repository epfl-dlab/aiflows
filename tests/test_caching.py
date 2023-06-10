import copy
import os
import shutil
import threading
import time

from src.flows import AtomicFlow
from src.utils import caching_utils
from src.utils.caching_utils import flow_run_cache

SLEEP_TIME = 0.1

TMP_CACHE_DIR = os.path.abspath(os.path.join(os.getcwd(), '.tmp_flow_cache'))
caching_utils.CACHING_PARAMETERS.cache_dir = TMP_CACHE_DIR


def prepare_flows_for_testing():
    class MyFlow(AtomicFlow):
        @flow_run_cache()
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

    return my_flow, task_message


def _time_run(flow, message):
    t0 = time.time()
    answer = flow(message)
    time_taken = time.time() - t0
    return answer, time_taken


def test_no_caching() -> None:
    shutil.rmtree(TMP_CACHE_DIR)
    caching_utils.CACHING_PARAMETERS.do_caching = False
    assert caching_utils.get_cache_dir() == TMP_CACHE_DIR

    my_flow, task_message = prepare_flows_for_testing()

    _ = my_flow(task_message)
    assert not os.path.exists(TMP_CACHE_DIR)


def test_simple_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = True
    my_flow, task_message = prepare_flows_for_testing()
    my_flow.run.clear_cache()

    data = copy.deepcopy(task_message.data)

    answer_0, first_time = _time_run(my_flow, task_message)
    assert first_time > SLEEP_TIME

    answer_1, second_time = _time_run(my_flow, task_message)
    assert second_time < SLEEP_TIME

    assert answer_1.data == answer_0.data
    assert answer_1.data["sum"] == data["v0"] + data["v1"]


def test_flow_state_modification_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = True
    my_flow, task_message = prepare_flows_for_testing()
    my_flow.run.clear_cache()
    data = copy.deepcopy(task_message.data)

    answer, runtime = _time_run(my_flow, task_message)
    assert answer.data["sum"] == data["v0"] + data["v1"]
    assert runtime > SLEEP_TIME

    my_flow.dry_run = True
    answer, runtime = _time_run(my_flow, task_message)
    assert answer.data["sum"] == 0
    assert runtime > SLEEP_TIME

    answer, runtime = _time_run(my_flow, task_message)
    assert answer.data["sum"] == 0
    assert runtime < SLEEP_TIME

    new_flow = my_flow.__class__.load_from_config(my_flow.flow_config)

    answer, runtime = _time_run(new_flow, task_message)
    assert answer.data["sum"] == data["v0"] + data["v1"]
    assert runtime < SLEEP_TIME

    new_flow.dry_run = True
    answer, runtime = _time_run(new_flow, task_message)
    assert answer.data["sum"] == 0
    assert runtime < SLEEP_TIME


def test_task_message_modification_caching() -> None:
    caching_utils.CACHING_PARAMETERS.do_caching = True
    my_flow, task_message = prepare_flows_for_testing()
    my_flow.run.clear_cache()
    data = copy.deepcopy(task_message.data)

    answer, runtime = _time_run(my_flow, task_message)
    assert answer.data["sum"] == data["v0"] + data["v1"]
    assert runtime > SLEEP_TIME

    new_task_message_same_data = my_flow.package_task_message(
        recipient_flow=my_flow,
        task_name="new-task",
        task_data=data,
        expected_outputs=["sum"]
    )

    answer, runtime = _time_run(my_flow, new_task_message_same_data)
    assert answer.data["sum"] == data["v0"] + data["v1"]
    assert runtime < SLEEP_TIME

    new_data = copy.deepcopy(data)
    new_data["v0"] = 15

    different_task = my_flow.package_task_message(
        recipient_flow=my_flow,
        task_name="task",
        task_data=new_data,
        expected_outputs=["sum"]
    )

    answer, runtime = _time_run(my_flow, different_task)
    assert answer.data["sum"] == new_data["v0"] + new_data["v1"]
    assert runtime > SLEEP_TIME

    answer, runtime = _time_run(my_flow, different_task)
    assert answer.data["sum"] == new_data["v0"] + new_data["v1"]
    assert runtime < SLEEP_TIME


def test_thread_safe():
    caching_utils.CACHING_PARAMETERS.do_caching = True
    if os.path.exists(caching_utils.CACHING_PARAMETERS.cache_dir):
        shutil.rmtree(caching_utils.CACHING_PARAMETERS.cache_dir)

    results = []
    results_cached = []

    def thread_task(incr):
        mf, ts = prepare_flows_for_testing()
        ts = copy.deepcopy(ts)
        ts.data["v0"] = ts.data["v0"] + incr

        # ~~~ first call not cached ~~~
        results.append(mf(ts).data["sum"])
        # ~~~ second call not cached ~~~
        results_cached.append(mf(ts).data["sum"])

    threads = []
    for i in range(5):
        thread = threading.Thread(target=thread_task, kwargs={"incr": i})
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    assert set(results) == set(results_cached)


# ToDo: test caching form different classes on the same cache

if __name__ == "__main__":
    test_thread_safe()
# test_no_caching()
# test_simple_caching()
# test_flow_state_modification_caching()
# test_task_message_modification_caching()
# test_composite_flow()
