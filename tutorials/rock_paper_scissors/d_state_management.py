from flows.base_flows.abstract import Flow
from tutorials.rock_paper_scissors.a_simple_flow import RockPaperScissorsPlayer
from tutorials.rock_paper_scissors.c_nesting import RockPaperScissorsJudge
from typing import List, Dict

if __name__=="__main__":
    judge = RockPaperScissorsJudge(name="RockPaperScissorsJudge", description="RockPaperScissorsJudge")
    print(f"In the beginning, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")

    task = judge.package_task_message(judge, "run", {}, output_keys=["A_score", "B_score", "n_rounds_played"])
    output = judge(task)
    print(f"After one task, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")

    # to reset a flow, you can call the reset method
    judge.reset()
    print(f"After resetting, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")

    # the reset method takes an optional full_reset=True argument
    # if you specify full_reset=False, everything except the flow_state is reset
    task = judge.package_task_message(judge, "run", {}, output_keys=["A_score", "B_score", "n_rounds_played"])
    output = judge(task)
    judge.helper_value = 22
    judge.reset(full_reset=False)
    print(f"After partial reset, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")
    try:
        print(judge.helper_value)
    except AttributeError:
        print("helper_value was deleted by reset")

