from flows.base_flows.abstract import Flow
from tutorials.rock_paper_scissors.a_simple_flow import RockPaperScissorsPlayer
from typing import List, Dict

class RockPaperScissorsJudge(Flow):
    """
    Minimal example of a Flow that contains other Flows
    """
    def __init__(self, **kwargs):
        super(RockPaperScissorsJudge, self).__init__(**kwargs)
    def initialize(self):
        # use flow_state to store the state of the flow
        self.flow_state["A"] = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")
        self.flow_state["B"] = RockPaperScissorsPlayer(name="Player B", description="RockPaperScissorsPlayer")
        self.flow_state["A_score"] = 0
        self.flow_state["B_score"] = 0
        self.flow_state["n_rounds_played"] = 0

    def run(self, input_data, output_keys) -> Dict:
        # the run method can include any logic you want
        # including calls to other flows
        flow_a = self.flow_state["A"]
        flow_b = self.flow_state["B"]

        # play 3 rounds of rock paper scissors
        for _ in range(3):

            # both player flows are called with a task message
            A_task = self.package_task_message(flow_a, "run", {}, output_keys=["choice"])
            A_output = flow_a(A_task)
            self._log_message(A_output)
            A_choice = A_output.data["choice"]

            B_task = self.package_task_message(flow_b, "run", {}, output_keys=["choice"])
            B_output = flow_b(B_task)
            self._log_message(B_output)
            B_choice = B_output.data["choice"]

            # you can change the state of the flow by writing to self.flow_state
            # if you use the _update_state method, a StateUpdateMessage message will be logged
            self._update_state({"n_rounds_played": self.flow_state["n_rounds_played"] + 1})

            if A_choice == B_choice:
                # neither has won
                pass
            elif (A_choice == "rock" and B_choice == "scissors"
                  or A_choice == "paper" and B_choice == "rock"
                  or A_choice == "scissors" and B_choice == "paper"):
                self._update_state({"A_score": self.flow_state["A_score"] + 1})
            else:
                self._update_state({"B_score": self.flow_state["B_score"] + 1})

        # at the end of run, you need to return a dictionary which has the expected outputs as keys
        # we offer a concenience method to extract the corresponding values from the flow_state
        return self._fetch_state_attributes_by_keys(output_keys, allow_class_attributes=False)

if __name__=="__main__":
    judge = RockPaperScissorsJudge(name="RockPaperScissorsJudge", description="RockPaperScissorsJudge")
    task = judge.package_task_message(judge, "run", {}, output_keys=["A_score", "B_score"])
    output = judge(task)

    print(f"player A won {output.data['A_score']} rounds")