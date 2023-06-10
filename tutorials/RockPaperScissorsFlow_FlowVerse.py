import flows
import flows.flow_verse

if __name__ == "__main__":
    # play 3 rounds of rock paper scissors
    repository_id = "martinjosifoski/CC_flows"
    RockPaperScissorsJudge = flows.flow_verse.load_flow(repository_id, name="RockPaperScissorsJudge")

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
