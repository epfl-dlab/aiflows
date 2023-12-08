from typing import Dict, Any

from aiflows.base_flows import CircularFlow
from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerExecutorFlow


class ReActWithHumanFeedback(ControllerExecutorFlow):
    @CircularFlow.output_msg_payload_processor
    def detect_finish_in_human_input(self, output_payload: Dict[str, Any], src_flow) -> Dict[str, Any]:
        human_feedback = output_payload["human_input"]
        if human_feedback.strip().lower() == "q":
            return {
                "EARLY_EXIT": True,
                "answer": "The user has chosen to exit before a final answer was generated.",
                "status": "unfinished",
            }

        return {"human_feedback": human_feedback}
