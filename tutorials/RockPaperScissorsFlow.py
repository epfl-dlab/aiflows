import random

from src.flows.abstract import Flow
from src.history import FlowHistory
from src.messages import TaskMessage
from typing import List


class RockPaperScissorsJudge(Flow):

    def __init__(self, **kwargs):
        super(RockPaperScissorsJudge, self).__init__(**kwargs)

        self.A = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")
        self.B = RockPaperScissorsPlayer(name="Player B", description="RockPaperScissorsPlayer")
        self.A_score = 0
        self.B_score = 0

    def run(self) -> bool:

        for round in range(3):
            A_task = self.package_task_message(self.A, "run", {}, expected_output_keys=["choice"])
            B_task = self.package_task_message(self.B, "run", {}, expected_output_keys=["choice"])
            # play another round
            A_output = self.A(A_task)
            self._log_message(A_output)
            B_output = self.B(B_task)
            self._log_message(B_output)

            A_choice = A_output.data["choice"]
            B_choice = B_output.data["choice"]

            if (A_choice == B_choice):
                # neither has won
                pass
            elif (A_choice == "rock" and B_choice == "scissors" \
                  or A_choice == "paper" and B_choice == "rock" \
                  or A_choice == "scissors" and B_choice == "paper"):
                self.A_score+= 1
            else:
                self.B_score += 1


class RockPaperScissorsPlayer(Flow):

    def __init__(self, **kwargs):
        super(RockPaperScissorsPlayer, self).__init__(**kwargs)

    def run(self, expected_output_keys: List[str] = None):

        choice = random.choice(["rock", "paper", "scissors"])

        self._update_state({"choice": choice})

if __name__=="__main__":

    # play 3 rounds of rock paper scissors
    judge = RockPaperScissorsJudge(name="Judge", description="RockPaperScissorsJudge")
    judge_task = judge.package_task_message(judge, "run", {}, expected_output_keys=["A_score"])
    judge_output = judge(judge_task)
    print(judge_output.data) # this is how often A wins

    # we create another judge, and copy over the state of the first
    another_judge = RockPaperScissorsJudge(name="Another Judge", description="RockPaperScissorsJudge")
    another_judge.__setstate__(judge.__getstate__())
    assert another_judge.A_score == judge.A_score

    # we play another 3 rounds of rock paper scissors
    another_judge_task = another_judge.package_task_message(another_judge, "run", {}, expected_output_keys=["A_score"])
    another_output = another_judge(another_judge_task)
    print(another_output.data)

    # ToDo: should we assert that the target flow actually matches the flow that's executing the task
    # there is a target_flow_run_id field in the task message
    # also: should we make sure that a task message is only used once?
    repeated_task_output = another_judge(judge_task)
    print(repeated_task_output.data)

    print("done")