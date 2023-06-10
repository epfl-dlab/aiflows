import random

from src.flows.abstract import Flow
from typing import List, Dict


class RockPaperScissorsJudge(Flow):

    def __init__(self, **kwargs):
        super(RockPaperScissorsJudge, self).__init__(**kwargs)

        self.flow_state["A"] = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")
        self.flow_state["B"] = RockPaperScissorsPlayer(name="Player B", description="RockPaperScissorsPlayer")
        self.flow_state["A_score"] = 0
        self.flow_state["B_score"] = 0
        self.flow_state["n_party_played"] = 0

    def run(self, input_data, expected_outputs) -> Dict:
        flow_a = self.flow_state["A"]
        flow_b = self.flow_state["B"]

        for _ in range(3):
            A_task = self.package_task_message(flow_a, "run", {}, expected_outputs=["choice"])
            B_task = self.package_task_message(flow_b, "run", {}, expected_outputs=["choice"])
            # play another round
            A_output = flow_a(A_task)
            self._log_message(A_output)
            B_output = flow_b(B_task)
            self._log_message(B_output)

            A_choice = A_output.data["choice"]
            B_choice = B_output.data["choice"]

            self._update_state({"n_party_played": self.flow_state["n_party_played"] + 1})

            if A_choice == B_choice:
                # neither has won
                pass
            elif (A_choice == "rock" and B_choice == "scissors"
                  or A_choice == "paper" and B_choice == "rock"
                  or A_choice == "scissors" and B_choice == "paper"):
                self._update_state({"A_score": self.flow_state["A_score"] + 1})
            else:
                self._update_state({"B_score": self.flow_state["B_score"] + 1})

        return self._get_keys_from_state(expected_outputs, allow_class_namespace=False)


class RockPaperScissorsPlayer(Flow):

    def __init__(self, **kwargs):
        super(RockPaperScissorsPlayer, self).__init__(**kwargs)

    def run(self, input_data, expected_outputs: List[str] = None):
        choice = random.choice(["rock", "paper", "scissors"])

        return {"choice": choice}


if __name__ == "__main__":
    # play 3 rounds of rock paper scissors
    judge = RockPaperScissorsJudge(name="Judge", description="RockPaperScissorsJudge")
    judge_task = judge.package_task_message(
        recipient_flow=judge,
        task_name="run",
        task_data={},
        expected_outputs=["A_score"]
    )
    judge_output = judge(judge_task)
    print(judge_output.data)  # this is how often A wins

    # we create another judge, and copy over the state of the first
    another_judge = RockPaperScissorsJudge(name="Another Judge", description="RockPaperScissorsJudge")
    another_judge.__setstate__(judge.__getstate__())
    assert another_judge.flow_state["A_score"] == judge.flow_state["A_score"]

    # we play another 3 rounds of rock paper scissors
    another_judge_task = another_judge.package_task_message(
        recipient_flow=another_judge,
        task_name="run",
        task_data={},
        expected_outputs=["A_score"]
    )

    another_output = another_judge(another_judge_task)
    print(another_output.data)

    # ToDo: should we assert that the target flow actually matches the flow that's executing the task
    # there is a target_flow_run_id field in the task message
    # also: should we make sure that a task message is only used once?
    repeated_task_output = another_judge(judge_task)
    print(repeated_task_output.data)

    print("done")
