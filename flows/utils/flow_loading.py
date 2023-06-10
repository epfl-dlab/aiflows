from typing import List

from omegaconf import DictConfig, OmegaConf
from flows import utils
import hydra
import copy

log = utils.get_pylogger(__name__)


def _identify_subflows(cfg: DictConfig) -> List[str]:
    subflow_keys = []

    for key in cfg.keys():
        # ~~~ Could not be a flow ~~~
        if type(cfg[key]) != dict:
            continue

        # ~~~ It is a flow if it should instantiate from src.flows.* ~~~
        if "_target_" in cfg[key].keys():
            if "src.flows" in cfg[key]["_target_"]:
                subflow_keys.append(key)

    return subflow_keys


def instantiate_flow(cfg: DictConfig):
    flow_config = copy.deepcopy(OmegaConf.to_container(cfg, resolve=True))

    subflow_names = _identify_subflows(flow_config)

    # ~~~ If it is an atomic flow, it does not have subflows ~~~
    if len(subflow_names) == 0:
        return hydra.utils.instantiate(flow_config, _convert_="partial")

    # ~~~ First instantiate subflows ~~~
    subflows = {}
    for sub_name in subflow_names:
        subflows[sub_name] = instantiate_flow(cfg[sub_name])
        del flow_config[sub_name]

    return hydra.utils.instantiate(flow_config, flows=subflows, _convert_="partial")
