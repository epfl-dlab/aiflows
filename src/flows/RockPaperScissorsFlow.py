import random

from src.flows.abstract import Flow
from src.history import FlowHistory
from src.messages import TaskMessage
from typing import List


class RockPaperScissorsJudge(Flow):
    def initialize(self):
        super(RockPaperScissorsJudge, self).initialize()
        self.state = {
            "rounds": 0,
            "A": RockPaperScissorsPlayer("Player A", "RockPaperScissorsPlayer"),
            "B": RockPaperScissorsPlayer("Player B", "RockPaperScissorsPlayer"),
            "A_score": 0,
            "B_score": 0,

        }
        self.history = FlowHistory()

    def step(self) -> bool:
        self.state["rounds"] += 1
        if self.state["rounds"] > 3:
            return True
        else:
            # play another round
            A_output = self.state["A"].run(expected_outputs=["choice"])
            self._log_message(A_output)
            B_output = self.state["B"].run(expected_outputs=["choice"])
            self._log_message(B_output)
            A_choice = A_output.data["choice"]
            B_choice = B_output.data["choice"]

            if (A_choice == B_choice):
                # neither has won
                pass
            elif (A_choice == "rock" and B_choice == "scissors" \
                  or A_choice == "paper" and B_choice == "rock" \
                  or A_choice == "scissors" and B_choice == "paper"):
                self.state["A_score"] += 1
            else:
                self.state["B_score"] += 1

            return False


class RockPaperScissorsPlayer(Flow):

    def expected_fields_in_state(self):
        return ["choice"]

    def run(self, expected_outputs: List[str] = None):
        #taskMessage = self._package_task_message(expected_output_keys=expected_outputs)
        #self._log_message(taskMessage)

        choice = random.choice(["rock", "paper", "scissors"])

        self.update_state({"choice": choice})

        output_message = self._package_output_message(expected_outputs=expected_outputs, parents=[])
        return output_message
