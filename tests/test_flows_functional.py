import pytest

from src.flows.abstract import Flow
from src.flows.RockPaperScissorsFlow import RockPaperScissorsJudge, RockPaperScissorsPlayer
from src.messages import TaskMessage, OutputMessage


def test_abstract_flow():
    flow = Flow("Abstract Flow", "Abstract Flow", [], [])

    # not implemented
    with pytest.raises(NotImplementedError):
        flow._flow()

def test_rock_paper_scissors():
    game = RockPaperScissorsJudge("Rock Paper Scissors", "Rock Paper Scissors", [], [])

    game.run(["A_score"])