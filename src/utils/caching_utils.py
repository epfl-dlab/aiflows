import functools
import pickle
from collections import OrderedDict
import os
import hashlib
from dataclasses import dataclass
from typing import Dict
import copy

from src.flows import Flow, AtomicFlow
from src.history import FlowHistory
from src.messages import TaskMessage
from pylogger import get_pylogger

log = get_pylogger(__name__)


@dataclass
class caching_parameters:
    max_cached_entries: int = 1000
    caching: bool = True
    cache_dir: str = None


class CachingResults:
    output_results: Dict
    full_state: Dict

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.output_results = state["output_results"]
        self.full_state = state["full_state"]



def get_cache_dir() -> str:
    # ~~~ Read in the global variable first ~~~
    cache_dir = caching_parameters.cache_dir
    if cache_dir:
        return str(cache_dir)

    # ~~~ Then read in the environment variables ~~~
    cache_dir = os.environ.get('CACHE_DIR')
    if cache_dir:
        return cache_dir

    # ~~~ Otherwise default to .cache in the local folder ~~~
    current_dir = os.getcwd()
    return os.path.abspath(os.path.join(current_dir, '.flow_cache'))


def load_cache(cache_dir: str = None) -> [Dict, str]:
    # ~~~ get cache_dir and create the dir if needed ~~~
    if cache_dir is None:
        cache_dir = get_cache_dir()

    assert os.path.isabs(cache_dir), \
        f"Invalid cache directory. It should be an absolute path: {cache_dir}."

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # ~~~ Load the cache from file ~~~
    files = os.listdir(cache_dir)
    if len(files) > 0:
        cache_file = os.path.join(cache_dir, files[0])
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
            assert type(cache) == OrderedDict, \
                f"Error when reading the cache file: {cache_file}. Expected type OrderedDict got {type(cache)}"
        return cache, cache_file
    else:
        return OrderedDict(), os.path.join(cache_dir, "cache.pkl")


def get_params(*args, **kwargs):
    from src.flows import Flow
    from src.messages import TaskMessage

    flow = None
    task_message = None

    all_args = list(args) + list(kwargs.values())

    for arg in all_args:
        if isinstance(arg, Flow):
            flow = arg

        if isinstance(arg, TaskMessage):
            task_message = arg

    assert flow, "Could not check in the cache because the flow was not given"
    assert task_message, "Could not check in the cache because the task message was not given"

    return flow, task_message


def compute_flow_run_key(flow, task_message):
    key = {"flow": repr(flow), "task_message": repr(task_message)}
    return hashlib.sha256(repr(key).encode("utf-8")).hexdigest()


# def flow_run_cache(max_number_entries: int = 1000):
def flow_run_cache(func):
    if not caching_parameters.caching:
        return func

    cache, cache_file = load_cache()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        flow, task_message = get_params(*args, **kwargs)
        key = compute_flow_run_key(flow, task_message)

        if key in cache:
            print(f"Flow call found in cache with hash key: {key}, skipping call.")

            value: CachingResults = cache.pop(key)
            cache[key] = value
            result = value.output_results
            flow.__setstate__(value.full_state)
            return result

        result = func(*args, **kwargs)
        caching_results = CachingResults()

        caching_results.output_results = result
        caching_results.full_state = copy.deepcopy(flow.__getstate__())

        cache[key] = caching_results

        if len(cache) > caching_parameters.max_cached_entries:
            cache.popitem(last=False)  # Remove the least recently used item

        # Save cache to file
        with open(cache_file, "wb") as file:
            pickle.dump(cache, file)

        return result

    def clear_cache():
        if not caching_parameters.caching:
            return

        print(f"Clearing cache: {cache_file}")
        cache.clear()
        try:
            os.remove(cache_file)
        except FileNotFoundError:
            pass

    wrapper.clear_cache = clear_cache
    return wrapper

    # return flow_cache_decorator


class MyFlow(AtomicFlow):
    @flow_run_cache
    def run(self, task_message: TaskMessage):
        log.info("current_run")
        if self.dry_run:
            answer = 0
        else:
            answer = 0
            for k, v in task_message.data.items():
                answer += v

        to_update = {self.expected_output_keys[0]: answer}
        self._update_state(to_update)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(expected_output_keys=self.expected_output_keys,
                                                      parent_message_ids=[task_message.message_id])
        return output_message


if __name__ == "__main__":
    @flow_run_cache
    def run(key_a, key_b):
        return int(key_a) + len(key_b)


    my_flow = MyFlow(
        name="my-flow",
        description="flow-sum",
        expected_outputs=["sum"],
        expected_inputs=["v0", "v1"],
    )

    task_message = TaskMessage(
        message_creator="task",
        parent_message_ids=[],
        flow_runner="task-runner",
        flow_run_id="0",
        data={"v0": 12, "v1": 23},
        expected_output_keys=["sum"],
        target_flow_run_id=my_flow.flow_run_id

    )

    log.info("test")

    answer = my_flow(task_message)
    print(f"Correct answer: {answer.data['sum'] == 35}")

    my_flow.dry_run = True
    answer = my_flow(task_message)
    print(f"Correct answer: {answer.data['sum'] == 0}")

    my_flow.name = "new-name"
    answer = my_flow(task_message)
    print(f"Correct answer: {answer.data['sum'] == 0}")

    my_flow.initialize()

    answer = my_flow(task_message)
    print(f"Correct answer: {answer.data['sum'] == 35}")

    my_flow.dry_run = True
    answer = my_flow(task_message)
    print(f"Correct answer: {answer.data['sum'] == 0}")

    my_flow.run.clear_cache()
