from typing import List

from src.flows.abstract import Flow
from src.messages import TaskMessage
from src.history import FlowHistory
import random

class RockPaperScissorsJudge(Flow):
    def initialize(self):
        self.state = {
            "rounds": 0,
            "A": RockPaperScissorsPlayer(),
            "B": RockPaperScissorsPlayer(),
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
            A_output = self.state["A"].run(TaskMessage(expected_outputs=["choice"]))
            self._log_message(A_output)
            B_output = self.state["B"].run(TaskMessage(expected_outputs=["choice"]))
            self._log_message(B_output)
            A_choice = A_output.data["choice"]
            B_choice = B_output.data["choice"]

            if(A_choice == B_choice):
                # neither has won
                pass
            elif(A_choice == "rock" and B_choice=="scissors" \
                    or A_choice == "paper" and B_choice=="rock" \
                    or A_choice == "scissors" and B_choice=="paper"):
                self.state["A_score"] += 1
            else:
                self.state["B_score"] += 1

            return False

    def run(self, taskMessage: TaskMessage):
        self._log_message(taskMessage)
        self.update_state(taskMessage)

        expected_outputs = taskMessage.expected_outputs

        choice = self.state["choice"]
        if choice == "rock":
            result = "tie"
        elif choice == "paper":
            result = "win"
        elif choice == "scissors":
            result = "lose"
        else:
            raise Exception("Invalid choice")

        self.update_state({"result": result})

        output_message = self._package_output_message(expected_outputs=expected_outputs)
        return output_message

class RockPaperScissorsPlayer(Flow):
    def run(self, taskMessage: TaskMessage):
        self._log_message(taskMessage)
        self.update_state(taskMessage)

        expected_outputs = taskMessage.expected_outputs

        choice = random.choice(["rock", "paper", "scissors"])

        self.update_state({"choice": choice})

        output_message = self._package_output_message(expected_outputs=expected_outputs)
        return output_message