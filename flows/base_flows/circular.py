from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
from flows.utils.general_helpers import validate_parameters
from ..utils import logging

log = logging.get_logger(__name__)



class CircularFlow(CompositeFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "reset_every_round", "early_exit_key"]
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        assert len(kwargs["subflows"]) > 0, f"Circular flow needs at least one flow, currently has 0"

    def _early_exit(self):
        early_exit_key = self.flow_config.get("early_exit_key", None)
        if early_exit_key:
            if early_exit_key in self.flow_state:
                return bool(self.flow_state[early_exit_key])
            elif early_exit_key in self.__dict__:
                return bool(self.__dict__[early_exit_key])

        return False

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        if "_status" in input_data:
            log.debug(f"input_data contains _status key={input_data['_status']}")
        input_data["_status"] = "unfinished"
        self._state_update_dict(update_data=input_data)

        max_round = self.flow_config.get("max_rounds", 1)

        output_message = self._sequential_run(input_data, max_round=max_round)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        # print(f"output keys: {self.get_output_keys()}")
        # outputs = self._fetch_state_attributes_by_keys(keys=output_message.data["output_keys"], #self.#get_mandatory_call_output_keys(),
        #                                                #TODO: the current doesn't work because the output_keys are "asnwer"
        #                                                # but at the moment, the answer is still called "observation"
        #                                                # and it will only be renamed in l522 in abstract_flow.py(ReActFlow)
        #                                                # workaround: use `output_message.data["output_keys"]` instead
        #
        #                                                # Further thoughts: maybe we should call data_transformation before _fetch_state_attributes_by_keys
        #                                                # as well as for input_data_transformation.
        #                                                allow_class_attributes=False)
        # import pdb; pdb.set_trace()
        run_output_keys = self.get_mandatory_run_output_keys()
        outputs = self._fetch_state_attributes_by_keys(keys=run_output_keys,
                                                       allow_class_attributes=False)

        return outputs

    @classmethod
    def type(cls):
        return "circular"

    def _sequential_run(self, initial_input_data: Dict[str, Any], max_round:int) -> Dict[str, Any]:
        # default value, though it should never be returned because max_round should be > 0
        last_output_data = initial_input_data
        output_message = {}
        for idx in range(max_round):
            for flow_name, current_flow in self.subflows:
                if self.flow_config["reset_every_round"].get(flow_name):
                    current_flow.reset(full_reset=True, recursive=True, src_flow=self)

                output_message = self._call_flow_from_state(
                    flow_to_call=current_flow)
                self._state_update_dict(update_data=output_message)
                last_output_data = output_message.data["output_data"]
                # ~~~ Check for end of interaction
                if self._early_exit():
                    log.info(f"[{self.flow_config['name']}] End of interaction detected")
                    self._state_update_dict(update_data={"_status": "finished"})
                    return output_message
        if max_round > 1:
            # ~~~ If max_round == 1, then there is not early exit, so we don't need to check for it
            log.info(f"[{self.flow_config['name']}] Max round reached. Returning output, answer might be incomplete.")
        return output_message

