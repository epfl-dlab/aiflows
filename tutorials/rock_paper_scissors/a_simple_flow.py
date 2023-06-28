from flows.base_flows.abstract import AtomicFlow
from typing import List, Dict
import random

class RockPaperScissorsPlayer(AtomicFlow):
    """
    Minimal example of an AtomicFlow
    """
    def __init__(self, **kwargs):
        super(RockPaperScissorsPlayer, self).__init__(**kwargs)

    def run(self, input_data, output_keys: List[str] = None):
        choice = random.choice(["rock", "paper", "scissors"])
        return {"choice": choice}

if __name__ == "__main__":
    # a flow instance must have a name and a description
    player = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")

    # the constructor will place its kwargs in the flow_config
    print(player.flow_config)

    # to create your own Flow, all you need to do is implement the run method
    print(player.run({}, output_keys=["choice"]))