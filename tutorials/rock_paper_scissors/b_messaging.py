from tutorials.rock_paper_scissors.a_simple_flow import RockPaperScissorsPlayer

if __name__=="__main__":
    player = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")

    # flows communicate via messages
    # to call the run method of another flow, you need to package a TaskMessage
    # flows are allowed to send themselves a TaskMessage, this serves as an entry point
    # a TaskMessage contains
    # - the recipient flow
    # - a description of the task
    # - input data
    # - a list of expected outputs
    task = player.package_task_message(player, "play one round", {}, expected_outputs=["choice"])
    output = player(task)

    # as a response to a task, a flow will send an OutputMessage
    # it contains metadata about the task execution, as well as results
    print(output.data['choice'])