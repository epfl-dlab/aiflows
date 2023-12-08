# ReAct With Human Feedback Tutorial
**Prequisites:** setting up your API keys (see [setting_up_aiFlows.md](./setting_up_aiFlows.md)), [Introducing the FlowVerse with a Simple Q&A Flow Tutorial](./intro_to_FlowVerse_minimalQA.md), [ReAct Tutorial](./reAct.md)

This guide introduces an implementation of the ReAct flow. It's organized in two sections:

1. [Section 1:](#section-1-whats-the-react-with-human-feedback-flow) What's The ReAct With Human Feedback Flow ?
2. [Section 2:](#section-2-running-the-react-with-human-feedback-flow) Running the ReAct With Human Feedback Flow

### By the Tutorial's End, I Will Have...

* Recognized the distinctions between ReAct and ReActWithHumanFeedback and their consequences
* Learned how to integrate a human feedback flow into ReAct
* Incorporated customized functions into the input and output interfaces.
* Grasped the limitations of ReAct, particularly its lack of long-term memory
* Deepened my understanding of the key parameters in the `ControllerExecutorFlow` configuration

## Section 1:  What's The ReAct With Human Feedback Flow ?

In the previous tutorial ([ReAct Tutorial](./reAct.md)), we introduced the ReAct flow. We noticed towards the end that, eventhough it works well, it can fail in some situations. For example, consider you ask the following:
> **Answer the following question: What is the profession and date of birth of Michael Jordan?**


In scenarios where the mentioned "Michael Jordan" refers to the Professor of Electrical Engineering and Computer Sciences and Professor of Statistics at Berkeley, ReAct may misinterpret it as the basketball player Michael Jordan and provide information about the latter. To address this, we can introduce an additional flow in our circular flow, allowing users to provide feedback on intermediate answers. This tutorial will guide you through the creation of the `ReActWithHumanFeedback` flow to handle such situations.

The `ReActWithHumanFeedback` flow is a circular flow that organizes the problem-solving process into three distinct flows:

1. `ControllerFlow`: With a specified goal and past observations from prior executions, the `ControllerFlow` makes decisions by choosing the next action from a predefined set. These actions are explicitly defined in the `ExecutorFlow` and contribute to progressing towards the defined goal. In our configuration, we implement the `ControllerFlow` using the `ChatAtomicFlow`.

2. `ExecutorFlow`:  Following the action selection by the `ControllerFlow`, the process moves to the `ExecutorFlow`. This is a branching flow that encompasses a set of subflows, with each subflow dedicated to a specific action. The `ExecutorFlow` executes the particular subflow associated with the action chosen by the `ControllerFlow`. In our setup, the `ExecutorFlow` includes the following individual flows:
    * `WikiSearchAtomicFlow`: This flow, given a "search term," executes a Wikipedia search and returns content related to the search term.
    * `LCToolFlow` using `DuckDuckGoSearchRun`: This flow, given a "query," queries the DuckDuckGo search API and retrieves content related to the query.

3. `HumanFeedbackFlow`: This flow prompts the user for feedback on the latest execution of the `ExecutorFlow`. The collected feedback is then conveyed back to the `ControllerFlow` to be considered in the subsequent execution step. Additionally, the flow is designed to have the capability to terminate the `ReActWithHumanFeedbackFlow` if the user expresses such a preference.

## Section 2: Running the ReAct With Human Feedback Flow

In this section, we'll guide you through running the `ReActWithHumanFeedbackFlow`. 

For the code snippets referenced from this point onward, you can find them [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/ReActWithHumanFeedback/).

Now, let's delve into the details without further delay!

Similar to the [Introducing the FlowVerse with a Simple Q&A Flow](./intro_to_FlowVerse_minimalQA.md) tutorial (refer to that tutorial for more insights), we'll start by fetching some flows from the FlowVerse. Specifically, we'll fetch the `ControllerExecutorFlowModule`, which includes the `ControllerExecutorFlow` (the composite flow of `ControllerFlow` and `ExecutorFlow`) and the `WikiSearchAtomicFlow`. Additionally, we'll fetch the `LCToolFlow`, a flow capable of implementing the DuckDuckGo search flow, and the `HumanStandardInputFlowModule`, a flow capable of gathering human feedback.

```python
from aiflows import flow_verse
# ~~~ Load Flow dependecies from FlowVerse ~~~
dependencies = [
    {"url": "aiflows/ControllerExecutorFlowModule", "revision": "main"},
    {"url": "aiflows/HumanStandardInputFlowModule", "revision": "main"},
    {"url": "aiflows/LCToolFlowModule", "revision": "main"},
]

flow_verse.sync_dependencies(dependencies)
```

If you've successfully completed the preceding tutorial, [ReAct Tutorial](./reAct.md), you are likely familiar with the fact that each flow within the FlowVerse is accompanied by a  `pip_requirements.txt` file detailing external library dependencies. To further explore this, examine the [pip_requirements.txt for the LCToolFlowModule](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/pip_requirements.txt),  the [pip_requirements.txt for the ControllerExecutorFlowModule](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/pip_requirements.txt), and the [pip_requirements.txt for the HumanStandardInputFlowModule](https://huggingface.co/aiflows/HumanStandardInputFlowModule/blob/main/pip_requirements.txt). You'll observe the necessity to install the following external libraries if they haven't been installed already:

```bash
pip install wikipedia==1.4.0
pip install langchain==0.0.336
pip install duckduckgo-search==3.9.6
```


Next, in order to empower the `HumanStandardInputFlow` to terminate the `ReActWithHumanFeedback` flow, it is essential to implement a function in the `ControllerExecutorFlow` class for this specific purpose. Consequently, a new class, `ReActWithHumanFeedback`, is introduced as follows (you can find it in [ReActWithHumandFeedback.py](https://github.com/epfl-dlab/aiflows/tree/main/examples/ReActWithHumanFeedback/ReActWithHumanFeedback.py)):


```python
from typing import Dict, Any

from aiflows.base_flows import CircularFlow
from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerExecutorFlow

class ReActWithHumanFeedback(ControllerExecutorFlow):
    @CircularFlow.output_msg_payload_processor
    def detect_finish_in_human_input(self, output_payload: Dict[str, Any], src_flow) -> Dict[str, Any]:
        human_feedback = output_payload["human_input"]
        if human_feedback.strip().lower() == "q":
            return {
                "EARLY_EXIT": True,
                "answer": "The user has chosen to exit before a final answer was generated.",
                "status": "unfinished",
            }

        return {"human_feedback": human_feedback}
```
Note that, we've simply added one function to the class which initiates the procedure to terminate the flow should the user enter "q"  when prompted for feedback.

The configuration for our flow is available in [ReActWithHumanFeedback.yaml](https://github.com/epfl-dlab/aiflows/tree/main/examples/ReActWithHumanFeedback/ReActWithHumanFeedback.yaml). We will now break it down into chunks and explain its various parameters. Note that the flow is instantiated from its default configuration, so we are only defining the parameters we wish to override here. The `ControllerExecutorFlow`'s default config  can be found [here](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/ControllerExecutorFlow.yaml) and the `LCToolFlow` default config can be found [here](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/LCToolFlow.yaml).

Our focus will be on explaining the modified parameters in the configuration, with reference to the previous tutorial for unchanged parameters.
Now let's look at the flow's configuration:
```yaml
max_rounds: 30
```
* `max_rounds`: The maximum number of rounds the flow can run for.

Now let's look at the flow's `subflows_config`, which provides configuration details for ReAct's subflows—`ControllerFlow`, the `ExecutorFlow` and the `HumanFeedbackFlow`:
```yaml
### Subflows specification
subflows_config:
  #ControllerFlow
  Controller:
    _target_: flow_modules.aiflows.ControllerExecutorFlowModule.ControllerAtomicFlow.instantiate_from_default_config
    backend:
      api_infos: ???
    commands:
      wiki_search:
        description: "Performs a search on Wikipedia."
        input_args: ["search_term"]
      ddg_search:
        description: "Query the search engine DuckDuckGo."
        input_args: ["query"]
      finish:
        description: "Signal that the objective has been satisfied, and returns the answer to the user."
        input_args: ["answer"]

    human_message_prompt_template:
      template: |2-
        Here is the response to your last action:
        {{observation}}
        Here is the feedback from the user:
        {{human_feedback}}
      input_variables:
        - "observation"
        - "human_feedback"
    input_interface_initialized:
      - "observation"
      - "human_feedback"

    previous_messages:
      first_k: 2 # keep the system prompt and the original goal
      last_k: 1 # keep only the last message
```
Note that the `ControllerFlow` configuration remains nearly identical to that in the previous tutorial, [ReAct Tutorial](./reAct.md). The only differences are:
*  The inclusion of an extra argument, "human_feedback," in both the `input_interface_initialized` parameter and the `input_variables` pararameter of the `human_message_prompt_template`. This is to incorporate the human's feedback in the message fed to the `ContollerFlow`
* Implementation of a mechanism to limit the number of `previous_messages` from the flow's chat history that is input to the Language Model (LLM). This limitation is crucial to prevent the Language Model (LLM) from exceeding the maximum token limit. Two parameters are overriden for this purpose:
  * `first_k`: Adds the first_k earliest messages of the flow's chat history to the input of the LLM.
  * `last_k`: Adds the last_k latest messages of the flow's chat history to the input of the LLM.M


```yaml
  #ExecutorFlow   
  Executor:
    _target_: aiflows.base_flows.BranchingFlow.instantiate_from_default_config
    subflows_config:
      wiki_search:
        _target_: flow_modules.aiflows.ControllerExecutorFlowModule.WikiSearchAtomicFlow.instantiate_from_default_config
      ddg_search:
        _target_: flow_modules.aiflows.LCToolFlowModule.LCToolFlow.instantiate_from_default_config
        backend:
          _target_: langchain.tools.DuckDuckGoSearchRun
```
The `ExecutorFlow` is identical to ReAct.
```yaml
  HumanFeedback:
    _target_: flow_modules.aiflows.HumanStandardInputFlowModule.HumanStandardInputFlow.instantiate_from_default_config
    request_multi_line_input_flag: False
    query_message_prompt_template:
      template: |2-
        Please provide feedback on the last step.

        Relevant information:
        == Goal ==
        {{goal}}

        == Last Command ==
        {{command}}

        == Args
        {{command_args}}

        == Result
        {{observation}}
      input_variables:
        - "goal"
        - "command"
        - "command_args"
        - "observation"
    input_interface:
      - "goal"
      - "command"
      - "command_args"
      - "observation"
```
`HumanFeedback`:
  * `request_multi_line_input_flag`: This boolean parameter determines whether the user/human is prompted to enter a multi-line input (True) or a single-line input (False).
  * `query_message_prompt_template`: This parameter involves a prompt template used to generate the message presented to the human. It includes:
      * `template`: The prompt template in Jinja format.
      * `input_variables` The input variables of the prompt. Note that these input variables have the same names as the placeholders "{{}}" in the `template`. Before querying the human, the template is rendered by placing the `input_variables` in the placeholders of the `template`.
  * `input_interface`:  Describes the expected input interface for the flow. It's noteworthy that the `input_interface` is identical to the `input_variables` of the `query_message_prompt_template`. This alignment is intentional, as they are passed as `input_variables` to the `query_message_prompt_template` to render the message presented to the user.


```yaml
topology: # The first two are the same as in the ControllerExecutorFlow
  - goal: "Select the next action and prepare the input for the executor."
    input_interface:
      _target_: aiflows.interfaces.KeyInterface
      additional_transformations:
        - _target_: aiflows.data_transformations.KeyMatchInput
    flow: Controller
    output_interface:
      _target_: ControllerExecutorFlow.detect_finish_or_continue
    reset: false

  - goal: "Execute the action specified by the Controller."
    input_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_rename:
        command: branch
        command_args: branch_input_data
      keys_to_select: ["branch", "branch_input_data"]
    flow: Executor
    output_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_rename:
        branch_output_data: observation
      keys_to_select: ["observation"]
    reset: false

  - goal: "Ask the user for feedback."
    input_interface:
      _target_: aiflows.interfaces.KeyInterface
    flow: HumanFeedback
    output_interface:
      _target_: ReActWithHumanFeedback.detect_finish_in_human_input
    reset: false

```
The default topology of the `ControllerExecutorFlow` is overriden here:
* For more details on topology, refer to the tutorial [Composite Flow](./composite_flow.md).
* The topology of the `ControllerExecutorFlow`'s  default config is available [here](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/ControllerExecutorFlow.yaml#L36). 
* Upon comparison with the default config's topology, one would observe that the sole alteration is the incorporation of the `HumanFeedbackFlow` to the circular flow.
* Note the significance of including the `detect_finish_in_human_input` function from the `ReActWithHumanFeedback` class in the output interface. This function, as defined earlier, plays a crucial role in initiating the process of terminating the flow if the human/user provides "q" as feedback.

Now that our configuration file is set up, we can proceed to call our flow. Begin by configuring your API information. Below is an example using an OpenAI key, along with examples for other API providers (in comment):

```python
# ~~~ Set the API information ~~~
# OpenAI backend
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
# Azure backend
# api_information = ApiInfo(backend_used = "azure",
#                           api_base = os.getenv("AZURE_API_BASE"),
#                           api_key = os.getenv("AZURE_OPENAI_KEY"),
#                           api_version =  os.getenv("AZURE_API_VERSION") )
````

Next, load the YAML configuration, insert your API information, 
and define the flow_with_interfaces dictionary:

```python
path_to_output_file = None
# path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk
root_dir = "."
cfg_path = os.path.join(root_dir, "ReActWithHumanFeedback.yaml")
cfg = read_yaml_file(cfg_path)
# put the API information in the config
cfg["subflows_config"]["Controller"]["backend"]["api_infos"] = api_information
flow = ReActWithHumanFeedback.instantiate_from_default_config(**cfg)

# ~~~ Instantiate the Flow ~~~
flow_with_interfaces = {
    "flow": flow,
    "input_interface": (
        None
        if cfg.get("input_interface", None) is None
        else hydra.utils.instantiate(cfg["input_interface"], _recursive_=False)
    ),
    "output_interface": (
        None
        if cfg.get("output_interface", None) is None
        else hydra.utils.instantiate(cfg["output_interface"], _recursive_=False)
    ),
}
```

Finally, run the flow with FlowLauncher.

```python
 data = {
        "id": 0,
        "goal": "Answer the following question: What is the profession and date of birth of Michael Jordan?",
}
# At first, we retrieve information about Michael Jordan the basketball player
# If we provide feedback, only in the first round, that we are not interested in the basketball player,
#   but the statistician, and skip the feedback in the next rounds, we get the correct answer

# ~~~ Run inference ~~~
path_to_output_file = None
# path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

_, outputs = FlowLauncher.launch(
    flow_with_interfaces=flow_with_interfaces,
    data=data,
    path_to_output_file=path_to_output_file,
)

# ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```

The complete example is accessible [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/ReActWithHumanFeedback/) and can be executed as follows:

```bash
cd examples/ReActWithHumanFeedback
python run.py
```

Upon execution, you will be prompted for feedback on the Executor's answer. The interaction will resemble the following:
```
Relevant information:
== Goal ==
Answer the following question: What is the profession and date of birth of Michael Jordan?

== Last Command ==
wiki_search

== Args
{'search_term': 'Michael Jordan'}

== Result
{'wiki_content': 'Michael Jeffrey Jordan (born February 17, 1963), also known by his initials MJ, is an American businessman and former professional basketball player. His profile on the official National Basketball Association (NBA) website states that "by acclamation, Michael Jordan is the greatest basketball player of all time." He played fifteen seasons in the NBA, winning six NBA championships with the Chicago Bulls. He was integral in popularizing the sport of basketball and the NBA around the world in the 1980s and 1990s, becoming a global cultural icon.Jordan played college basketball for three seasons under coach Dean Smith with the North Carolina Tar Heels. As a freshman, he was a member of the Tar Heels\' national championship team in 1982. Jordan joined the Bulls in 1984 as the third overall draft pick and quickly emerged as a league star, entertaining crowds with his prolific scoring while gaining a reputation as one of the game\'s best defensive players. His leaping ability, demonstrated by performing slam dunks from the free-throw line in Slam Dunk Contests, earned him the nicknames "Air Jordan" and "His Airness". Jordan won his first NBA title with the Bulls in 1991 and followed that achievement with titles in 1992 and 1993, securing a three-peat. Jordan abruptly retired from basketball before the 1993–94 NBA season to play Minor League Baseball but returned to the Bulls in March 1995 and led them to three more championships in 1996, 1997, and 1998, as well as a then-record 72 regular season wins in the 1995–96 NBA season. He retired for the second time in January 1999 but returned for two more NBA seasons from 2001 to 2003 as a member of the Washington Wizards. During his professional career, he was also selected to play for the United States national team, winning four gold medals—at the 1983 Pan American Games, 1984 Summer Olympics, 1992 Tournament of the Americas and 1992 Summer Olympics—while also being undefeated.Jordan\'s individual accolades and accomplishments include six NBA Finals Most Valuable Player (MVP) awards, ten NBA scoring titles (both all-time records), five NBA MVP awards, ten All-NBA First Team designations, nine All-Defensive First Team honors, fourteen NBA All-Star Game selections, three NBA All-Star Game MVP awards, three NBA steals titles, and the 1988 NBA Defensive Player of the Year Award. He holds the NBA records for career regular season scoring average (30.1 points per game) and career playoff scoring average (33.4 points per game). In 1999, he was named the 20th century\'s greatest North American athlete by ESPN and was second to Babe Ruth on the Associated Press\' list of athletes of the century. Jordan was twice inducted into the Naismith Memorial Basketball Hall of Fame, once in 2009 for his individual career, and again in 2010 as part of the 1992 United States men\'s Olympic basketball team ("The Dream Team"). He became a member of the United States Olympic Hall of Fame in 2009, a member of the North Carolina Sports Ha'}

[2023-12-06 09:30:40,844][aiflows.aiflows.HumanStandardInputFlowModule.HumanStandardInputFlow:126][INFO] - Please enter you single-line response and press enter.
```

You can respond with:

```
No I'm talking about Michael Irwin Jordan. I think he's a statistician. Maybe look him up on wikipedia?
```

Subsequently, ReAct will provide a response similar to this:
```
Relevant information:
== Goal ==
Answer the following question: What is the profession and date of birth of Michael Jordan?

== Last Command ==
wiki_search

== Args
{'search_term': 'Michael Irwin Jordan'}

== Result
{'wiki_content': 'Michael Irwin Jordan  (born February 25, 1956) is an American scientist, professor at the University of California, Berkeley and researcher in machine learning, statistics, and artificial intelligence.Jordan was elected a member of the National Academy of Engineering in 2010 for contributions to the foundations and applications of machine learning.\nHe is one of the leading figures in machine learning, and in 2016 Science reported him as the world\'s most influential computer scientist.In 2022, Jordan won the inaugural World Laureates Association Prize in Computer Science or Mathematics, "for fundamental contributions to the foundations of machine learning and its application."\n\n\n== Education ==\nJordan received his BS magna cum laude in Psychology in 1978 from the Louisiana State University, his MS in Mathematics in 1980 from Arizona State University and his PhD in Cognitive Science in 1985 from the University of California, San Diego. At the University of California, San Diego, Jordan was a student of David Rumelhart and a member of the Parallel Distributed Processing (PDP) Group in the 1980s.\n\n\n== Career and research ==\nJordan is the Pehong Chen Distinguished Professor at the University of California, Berkeley, where his appointment is split across EECS and Statistics. He was a professor at the Department of Brain and Cognitive Sciences at MIT from 1988 to 1998.In the 1980s Jordan started developing recurrent neural networks as a cognitive model. In recent years, his work is less driven from a cognitive perspective and more from the background of traditional statistics.\nJordan popularised Bayesian networks in the machine learning community and is known for pointing out links between machine learning and statistics. He was also prominent in the formalisation of variational methods for approximate inference and the popularisation of the expectation–maximization algorithm in machine learning.\n\n\n=== Resignation from Machine Learning ===\nIn 2001, Jordan and others resigned from the editorial board of the journal Machine Learning. In a public letter, they argued for less restrictive access and pledged support for a new open access journal, the Journal of Machine Learning Research, which was created by Leslie Kaelbling to support the evolution of the field of machine learning.\n\n\n=== Honors and awards ===\nJordan has received numerous awards, including a best student paper award (with X. Nguyen and M. Wainwright) at the International Conference on Machine Learning (ICML 2004), a best paper award (with R. Jacobs) at the American Control Conference (ACC 1991), the ACM-AAAI Allen Newell Award, the IEEE Neural Networks Pioneer Award, and an NSF Presidential Young Investigator Award. In 2002 he was named an AAAI Fellow "for significant contributions to reasoning under uncertainty, machine learning, and human motor control." In 2004 he was named an IMS Fellow "for contributions to graphical models and machine learning." In 2005 he was named an IEEE Fellow "for '}
[2023-12-06 09:53:52,058][aiflows.aiflows.HumanStandardInputFlowModule.HumanStandardInputFlow:126][INFO] - Please enter you single-line response and press enter.
```
Your subsequent response could be:

```
There you go! I think you have it!
```
Eventually, the flow should terminate and return something similar to:

```
[{'answer': 'Michael Jordan is a scientist, professor, and researcher in machine learning, statistics, and artificial intelligence. He was born on February 25, 1956.', 'status': 'finished'}]
```

Finally, it provides the correct answer!


Nevertheless, persisting with the use of `ReActWithHumanFeedback` may reveal an inherent challenge, particularly in prolonged conversations. The primary issue arises when attempting to pass the entire message history to the language model (LLM), eventually surpassing the maximum token limit allowable. As a workaround, we currently send only the first two and the last messages as context to the LLM. However, this approach is suboptimal if you desire your model to maintain a more comprehensive long-term memory.

To address this limitation, we recommend exploring the subsequent tutorial, [AutoGPT Tutorial](./autogpt_tutorial.md). This tutorial introduces a fundamental implementation of AutoGPT, enhancing the ReAct flow by incorporating a Memory Flow. This addition tackles the challenge of managing longer conversations.

___


**Next Tutorial:** [AutoGPT Tutorial](./autogpt_tutorial.md)