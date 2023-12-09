# AutoGPT Tutorial
**Prequisites:** setting up your API keys (see [setting_up_aiFlows.md](./setting_up_aiFlows.md)), [Introducing the FlowVerse with a Simple Q&A Flow Tutorial](./intro_to_FlowVerse_minimalQA.md), [ReAct Tutorial](./reAct.md), [React With Human Feedback Tutorial](./reActwHumanFeedback.md)

This guide introduces an implementation of the AutoGPT flow. It's organized in two sections:

1. [Section 1:](#section-1-whats-the-autogpt-flow) What's The AutoGPT flow ?
2. [Section 2:](#section-2-running-the-autogpt-flow) Running the AutoGPT Flow

### By the Tutorial's End, I Will Have...

* Acknowledged the differences between AutoGPT and ReActWithHumanFeedback and their implications
* Gained proficiency in executing the AutoGPTFlow
* Enhanced comprehension of intricate flow structures

## Section 1: What's The AutoGPT flow ?

In the previous tutorial [React With Human Feedback Tutorial](./reActwHumanFeedback.md), we introduced the `ReActWithHumanFeedback` Flow. Towards the end, while the flow demonstrated effective functionality, we observed a notable challenge, especially in prolonged conversations. The principal issue emerged when attempting to transmit the entire message history to the language model (LLM), eventually surpassing the permissible maximum token limit. As a temporary solution, we opted to send only the first two and the last messages as context to the LLM. However, this approach proves suboptimal if your objective is to enable the model to maintain a more comprehensive long-term memory.  Consequently, in this tutorial, we will demonstrate how to create a basic implementation of the `AutoGPT` flow, providing a solution to tackles this issue.

The `AutoGPT` flow is a circular flow that organizes the problem-solving process into four distinct flows:

1. `ControllerFlow`: Given an a goal and observations (from past executions), it selects from a predefined set of actions, which are explicitly defined in the `ExecutorFlow`, the next action it should execute to get closer accomplishing its goal. In our configuration, we implement the `ControllerFlow` using the `ChatAtomicFlow`

2. `ExecutorFlow`:  Following the action selection by the `ControllerFlow`, the process moves to the `ExecutorFlow`. This is a branching flow that encompasses a set of subflows, with each subflow dedicated to a specific action. The `ExecutorFlow` executes the particular subflow associated with the action chosen by the `ControllerFlow`. In our setup, the `ExecutorFlow` includes the following individual flows:
    * `WikiSearchAtomicFlow`: This flow, given a "search term," executes a Wikipedia search and returns content related to the search term.
    * `LCToolFlow` using `DuckDuckGoSearchRun`: This flow, given a "query," queries the DuckDuckGo search API and retrieves content related to the query.

3. `HumanFeedbackFlow`: This flow prompts the user for feedback on the latest execution of the `ExecutorFlow`. The collected feedback is then conveyed back to the `ControllerFlow` to be considered in the subsequent execution step. Additionally, the flow is designed to have the capability to terminate the `ReActWithHumanFeedbackFlow` if the user expresses such a preference.

4. `MemoryFlow`: This flow is used to read and write and read memories stored of passed conversations in a database. These memories can be passed to the `ControllerFlow` enabling it to have a long term memory without having to transmit the entire message history to the language model (LLM). It's implemented with the `VectorStoreFlow`

Here's a broad overview of the  `AutoGPTFlow`:

```
| -------> Memory Flow -------> Controller Flow ------->|
^                                                       |      
|                                                       |
|                                                       v
| <----- HumanFeedback Flow <------- Executor Flow <----|
```

## Section 2 Running the AutoGPT Flow

In this section, we'll guide you through running the ReActWithHumanFeedbackFlow.

For the code snippets referenced from this point onward, you can find them [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/AutoGPT/).

Now, let's delve into the details without further delay!

Similar to the [Introducing the FlowVerse with a Simple Q&A Flow](./intro_to_FlowVerse_minimalQA.md) tutorial (refer to that tutorial for more insights), we'll start by fetching some flows from the FlowVerse. Specifically, we'll fetch the `AutoGPTFlowModule`, which includes `ControllerFlow`, `ExecutorFlow`, and the `WikiSearchAtomicFlow`. Additionally, we'll fetch the `LCToolFlow`, a flow capable of implementing the DuckDuckGo search flow.

```python
from aiflows import flow_verse
# ~~~ Load Flow dependecies from FlowVerse ~~~
dependencies = [
    {"url": "aiflows/AutoGPTFlowModule", "revision": "main"},
    {"url": "aiflows/LCToolFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
```

If you've successfully completed the [ReAct Tutorial](./reAct.md), you are likely familiar with the fact that each flow within the FlowVerse is accompanied by a  `pip_requirements.txt` file detailing external library dependencies. To further explore this, examine the [pip_requirements.txt for the LCToolFlowModule](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/pip_requirements.txt), and the [pip_requirements.txt for the AutoGPTFlowModule](https://huggingface.co/aiflows/AutoGPTFlowModule/blob/main/pip_requirements.txt). You'll observe the necessity to install the following external libraries if they haven't been installed already:

```bash
pip install duckduckgo-search==3.9.6
pip install wikipedia==1.4.0 
pip install langchain==0.0.336 
pip install chromadb==0.3.29
pip install faiss-cpu==1.7.4
```

Now that we've fetched the flows from the FlowVerse and installed their respective requirements, we can start creating our Flow.

The configuration for our flow is available in [AutoGPT.yaml](https://github.com/epfl-dlab/aiflows/tree/main/examples/AutoGPT/AutoGPT.yaml). We will now break it down into chunks and explain its various parameters. Note that the flow is instantiated from its default configuration, so we are only defining the parameters we wish to override here. `AutoGPTFlow`'s default config  can be found [here](https://huggingface.co/aiflows/AutoGPTFlowModule/blob/main/AutoGPTFlow.yaml), the `LCToolFlow` default config can be found [here](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/LCToolFlow.yaml) and memory's flow default config `VectorStoreFlow` can be found [here](https://huggingface.co/aiflows/VectorStoreFlowModule/blob/main/VectorStoreFlow.yaml)

Our focus will be on explaining the modified parameters in the configuration, with reference to the [ReAct With Human Feedback Tutorial](./reActwHumanFeedback.md) Tutorial for unchanged parameters.
Now let's look at the flow's configuration:
```yaml
flow:
  _target_: flow_modules.aiflows.AutoGPTFlowModule.AutoGPTFlow.instantiate_from_default_config
  max_rounds: 30
```
* `_target_`: We're instantiating `AutoGPTFlow` with its default configuration and introducing some overrides, as specified below.
* `max_rounds`: The maximum number of rounds the flow can run for.

Now let's look at the flow's `subflows_config`, which provides configuration details for ReAct's subflows—`ControllerFlow`, the `ExecutorFlow`, the `HumanFeedbackFlow` and the `MemoryFlow`:
```yaml
  ### Subflows specification
  subflows_config:
    #ControllerFlow Configuration
    Controller:
      _target_: flow_modules.aiflows.ControllerExecutorFlowModule.ControllerAtomicFlow.instantiate_from_default_config
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
      backend:
        api_infos: ???
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
        last_k: 1
        first_k: 2
```
The `ControllerFlow` is identical to `ReActWithHumanFeedback`.
```yaml
    #ExecutorFlow Configuration
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
The `ExecutorFlow` is identical to `ReActWithHumanFeedback` and `ReAct`.
```yaml
    #MemoryFlow Configuration
    Memory:
      backend:
        model_name: none
        api_infos: ???
```
The `MemoryFlow`, primarily instantiated from [AutoGPT's defaut configuration](https://huggingface.co/aiflows/AutoGPTFlowModule/blob/main/AutoGPTFlow.yaml#L87).Additionally, please refer to the `MemoryFlow`'s [FlowCard](https://huggingface.co/aiflows/VectorStoreFlowModule) for more details.

With our configuration file in place, we can now proceed to call our flow. Begin by configuring your API information. Below is an example using an OpenAI key, along with examples for other API providers (commented):

```python
# ~~~ Set the API information ~~~
# OpenAI backend
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
# Azure backend
# api_information = ApiInfo(backend_used = "azure",
#                           api_base = os.getenv("AZURE_API_BASE"),
#                           api_key = os.getenv("AZURE_OPENAI_KEY"),
#                           api_version =  os.getenv("AZURE_API_VERSION") )

```

Next, load the YAML configuration, insert your API information, and define the `flow_with_interfaces` dictionary as shown below:

```python
cfg = read_yaml_file(cfg_path)
    
# put the API information in the config
cfg["flow"]["subflows_config"]["Controller"]["backend"]["api_infos"] = api_information
cfg["flow"]["subflows_config"]["Memory"]["backend"]["api_infos"] = api_information
# ~~~ Instantiate the Flow ~~~
flow_with_interfaces = {
    "flow": hydra.utils.instantiate(cfg["flow"], _recursive_=False, _convert_="partial"),
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
Lastly, execute the flow using the FlowLauncher.
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

The complete example is accessible [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/AutoGPT/) and can be executed as follows:

```bash
cd examples/AutoGPT
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

Congratulations you've succesfully run `AutoGPTFlow` !
