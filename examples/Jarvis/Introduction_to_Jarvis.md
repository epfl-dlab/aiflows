## Introduction to Jarvis

Jarvis is a general purpose agent empowered by a hierarchical structure of large language models and tools including a code interpreter. At a high level, Jarvis takes in tasks in natural language, and achieve the task by making plans, writing and executing code.



To allow for extended the lifespan of Jarvis (constrained by token limitations of LLM APIs) and enable Jarvis to be able to utilize previously accomplished results, we implemented some interesting memory management mechanisms.


**Notice:**
The code interpreter of Jarvis (https://huggingface.co/Tachi67/InterpreterFlowModule) relies on **open-interpreter** (https://github.com/KillianLucas/open-interpreter). We are extracting the specific code from open-interpreter because the litellm version of open-interpreter is not compatible with that of the current version of aiflows (v.0.1.7).



### Structure of Jarvis

Let's cut things short, here is an illustration of the Jarvis architecture:
```
     goal, memory_files (dict)
             |
             v
    +-------------------+
    |  MemoryReading    |  Reads in the content of the memory files
    |    Flow           |
    +-------------------+
             |
             | (memory_content)
             |
             v
    +-------------------+
    |    PlanWriter     |  Writes a step-by-step plan to achieve the goal
    +-------------------+
             |
             | (plan)
             |
             v
    +-------------------+
    |   CtrlExMemFlow   |  Illustrated below. Carries out the plan in an controller-executor fashion,
    |                   |  with memory management mechanisms.
    +-------------------+
             |
    (summary, result)

```

Here is the structure of the `CtrlExMemFlow`:
```
    plan, memory_files, memory_content, goal
                |
                v
        +---------------+
        |  Controller   | --------<<<<-----------+
        +---------------+                        |
                |                                |
                | (command, command args)        |
                |                                |
                v                                |
        +------------------+                     |
        |   Executor       |  Each branch is an  |
        | (Tree Structure) |  executor           |
        +------------------+                     |
                |                                ^
                | (execution results)            ^
                |                                ^
                v                                ^
        +---------------+                        ^
        | MemWriteFlow  |  Updates memory files  ^
        +---------------+                        ^
                |                                ^
                | (summary)                      |
                |                                |
                v                                |
        +---------------+                        |
        | MemReadFlow   |  Reads updated memory  |
        +---------------+                        |
                |                                |
                | (updated memory content)       |
                |                                |
                +-> goes back to the Controller>-+

```
Structure of the Executors:
```
             +-------------------+
             |   Branching       |
             |    Executor       |
             +-------------------+
        /     |     |     |     |      \
       /      |     |     |     |       \
      /       |     |     |     |        \
     /        |     |     |     |         \
Coder  ask_user re_plan update_plan intermediate_answer final_answer

```

In fact, this structure is defined as [AbstractBoss](https://huggingface.co/Tachi67/AbstractBossFlowModule), Jarvis inherits from this abstract flow. There are other components that
inherits from this structure. for example, [Coder](https://huggingface.co/Tachi67/CoderFlowModule), [ExtendLibrary](https://huggingface.co/Tachi67/ExtendLibraryFlowModule)

Let's go through some basic ideas of Jarvis and its components now.
- memory: Jarvis should remember certain important memory, they include the plan (`plan`), and the history of subflows execution results (`logs`). To do this, we put them in external files, and inject them into the system prompts to controllers and other corresponding roles. There are other classes that inherits from `AbstractBoss` and have other memories, e.g. `Coder` takes the memory of `code_libarary`, which is the function signatures and docstrings of the code written by the Coder and saved in the code library.
- memory_files: A dictionary: `{memory_name: memory_file_path}`
- [MemoryReadingFlow](https://huggingface.co/Tachi67/MemoryReadingFlowModule): Reads in the content of the memory files.
- [PlanWriter](https://huggingface.co/Tachi67/PlanWriterFlowModule): Writes a step-by-step plan to achieve the goal in an interactive fashion. During the process of writing a plan, the user has the chance to provide feedback to or directly edit the plan just written. The PlanWriter can comprehend the user's action and make adjustments to the plan accordingly.
- [CtrlExMem_JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/CtrlExMem_JarvisFlow.py): Inherits from [CtrlExMemFlow](https://huggingface.co/Tachi67/AbstractBossFlowModule/blob/main/CtrlExMemFlow.py), it executes the step-by-step plan written by the PlanWriter in a controller-executor fashion, with memory management mechanisms.
- [Controller of CtrlExMem_JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/Controller_JarvisFlow.py): The controller of the CtrlExMem_JarvisFlow. It inherits from [ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule) (that being said, an LLM API), it decides to either call one of the branching executors or to finish and exit the loop.
- [Coder](https://huggingface.co/Tachi67/CoderFlowModule): One branch of the executors, it writes functions that are reusable to the code library (Python), writes and run code scripts of execute logics like executing one function from the library, installing packages, etc.
- [re_plan](https://huggingface.co/Tachi67/ReplanningFlowModule): One branch of the executors, when something goes wrong, re-draft the plan.
- [update_plan](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/UpdatePlanAtomicFlow.py): One branch of the executors, when the controller realizes that one (or some, depending on the LLM's response) step of the plan is (are) done, it generates a new plan that marks the step(s) as done.
- [ask_user](https://huggingface.co/Tachi67/ExtendLibraryFlowModule/blob/main/ExtLibAskUserFlow.py): One branch of the executors, when the controller needs user assist, confirmation, etc., it calls this flow.
- [intermediate_answer](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/IntermediateAns_Jarvis.py): One branch of the executors, when one (or some, depending on the LLM's response) step of the plan is (are) done, the controller calls this flow to remind the user that the step(s) is (are) done, and ask for the user's feedback.
- [final_answer](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/FinalAns_Jarvis.py): One branch of the executors, when the plan is done, the controller calls this flow to remind the user that the plan is done, and ask for the user's feedback.
- [MemWriteFlow](https://huggingface.co/Tachi67/MemoryWritingFlowModule): Updates memory files (`logs`).
- [MemReadFlow](https://huggingface.co/Tachi67/MemoryReadingFlowModule): Reads updated memory files (`plan`,`logs`).


### Memory Management Mechanisms
For long-term memory, the goal is to refine the quality of LLM's chat history, to do this, we utilize memory files, for now there are three kinds of memory_files:
- `plan`: the step-by-step plan to achieve the goal, it will be updated by the `update_plan` executor when the controller realizes that one (or some, depending on the LLM's response) step of the plan is (are) done.
- `logs`: the history of subflows execution results, it will be updated by the `MemWriteFlow` executor whenever one branching executor is finished.
- `code_library`: the function signatures and docstrings of the code written by the Coder and saved in the code library, it will be updated by the `Coder` executor whenever the Coder writes a new function to the code library.

The memory contents are injected into the system prompts of the respective LLM chats.

We also applied a sliding window for history chat messages as a workaround for the token limitations of the LLM APIs. To do this:
- Whenever the chat that utilizes the sliding window is called, we inject a new system prompt with the newest memory (plan, logs, for `Coder` and some other flows, `code_library` is also injected) into the chat history.)
- We crop the chat history with a tailing window of length 3, that will include the assistant's previous call, the updated system prompt, the the user's new response.

As a result, Jarvis is able to run for quite a long time, and it's able to use the code written before.

### An Example run of Jarvis
WARNING: This section is quite lengthy. Also, due to the nondeterministic nature of the LLMs, the results may vary, the reader is suggested to make sure every plan and piece of code does the same thing as the example presents.

- user input goal = "Download tesla's stock prices from 2022-01-01 to 2022-06-01 from yfinance, plot the prices."
- Plan of Jarvis is generated, the user is able to edit the plan directly or give feedback.
    
    Plan (Jarvis):
    1. Write and run code to download Tesla's stock prices from 2022-01-01 to 2022-06-01 using python package yfinance.
    2. Write and run code to plot the downloaded stock prices using matplotlib.
    3. Give a final answer to the user.
- Controller of Jarvis calls Coder.
- Planner of Coder generates plan of Coder, the user is able to edit the plan directly or give feedback.
  
    Plan (Coder):
    1. Extend the code library with a function named `download_stock_data`. This function should take three parameters: `ticker_symbol` (a string representing the stock's ticker symbol), `start_date` (a string representing the start date in the format 'YYYY-MM-DD'), and `end_date` (a string representing the end date in the same format). The function should use the `yfinance` library to download the stock data for the given ticker symbol between the start and end dates, and return this data as a pandas DataFrame.

    2. Run a code script to import the `yfinance` library. If the library is not already installed, the script should install it using pip.

    3. Run a code script to import the `download_stock_data` function from the code library.

    4. Run a code script to call the `download_stock_data` function with the inputs 'TSLA', '2022-01-01', and '2022-06-01'. The script should store the returned DataFrame in a variable.

    5. Give a final answer: the data is stored in a variable, specify the variable name.

- The Controller of Coder calls ExtendLibraryFlow.
- Planner of ExtendLibrary generates plan of ExtendLibraryFlow, the user is able to edit the plan directly or give feedback.
    
    Plan (ExtendLibrary):
    1. Write a function named 'download_stock_data'. This function should take three parameters: 'ticker_symbol' (a string), 'start_date' (a string in the format 'YYYY-MM-DD'), and 'end_date' (a string in the same format). Inside the function, use the 'yfinance.download' method from the 'yfinance' library to download the stock data for the given ticker symbol between the start and end dates. The 'yfinance.download' method should be called with the 'ticker_symbol' as the first argument, 'start_date' as the second argument and 'end_date' as the third argument. The function should return the downloaded data as a pandas DataFrame.


- The Controller of ExtendLibrary calls write_code, inside of write_code flow:
  -  The code gets generated, and the user is able to provide feedback on the code or edit the code directly.

    Code:
    ```python
    def download_stock_data(ticker_symbol: str, start_date: str, end_date: str):
        """
        Downloads the stock data for the given ticker symbol between the start and end dates.

        Parameters:
        ticker_symbol (str): The ticker symbol of the stock.
        start_date (str): The start date in the format 'YYYY-MM-DD'.
        end_date (str): The end date in the format 'YYYY-MM-DD'.

        Returns:
        pandas.DataFrame: The downloaded stock data.
        """
        import yfinance

        # Download the stock data
        data = yfinance.download(ticker_symbol, start=start_date, end=end_date)

        return data
    ```
  -  The code is tested, before testing the code, the user is able to provide test suites to test the code, otherwise only the syntax of the code is checked. Here we do not provide any other test suites.
- The Controller calls save_code to append the newly written function to the code library.
- The Controller of ExtendLibrary calls update_plan to mark the step of plan as done.
- The Controller of ExtendLibrary finishes ExtendLibraryFlow, going back to the coder.
- When finishing the ExtendLibraryFlow, it is reseted, setting its flow_state and the flow_state of its subflows as an empty dict.
- The Controller of Coder calls update_plan to mark step 1 of the plan as done.
- The Controller of Coder calls run_code to proceed step 2 of the plan. The code to run is generated by the Controller of Coder.
- Inside of run_code, the following is executed:
  - The code is written to a temp file.
  ```shell
  pip install yfinance
  ```
  - The temp file is opened in a vscode session.
  - The user is able to edit the code.
  - Code is ran by an interpreter.
  - The result is logged to the console, the user is able to provide feedback on the execution result.
  - Exit back to Coder.

- The Controller of Coder calls run_code to proceed step 3 of the plan.
- Code to import function is executed, the user is able to provide feedback.
    
    ```python
    import importlib
    import library
    importlib.reload(library)
    from library import download_stock_data
    ```
- The Controller of Coder calls run_code to proceed step 4 of the plan.
- Code to download the data is executed. User is able to provide feedback on the results.
  
  ```python
  stock_data = download_stock_data('TSLA', '2022-01-01', '2022-06-01')
  ```
- The Controller of Coder calls update_plan to mark the rest steps of the plan as done.
- The Controller finishes the Coder flow and return result to the JarvisFlow.
- When finishing, the CoderFlow resets, setting its flow_state and the flow_state of its subflows an an empty dict.
- The Controller of Jarvis calls update_plan to mark step 1 of the plan as done.
- The Controller of Jarvis calls Coder with the goal of the second step of plan.
- The Planner of Coder makes a plan:
    
    Plan:
   1. Extend the code library with a function to plot the stock prices. The function should take a pandas DataFrame (which is the output of the download_stock_data function) as input and plot the 'Close' prices against the dates. The function should not return anything. The function should be named 'plot_stock_prices'. 
   2. Import the 'download_stock_data' and 'plot_stock_prices' functions from the code library. 
   3. Run the 'download_stock_data' function with the desired ticker symbol, start date, and end date to get the stock data. 
   4. Run the 'plot_stock_prices' function with the DataFrame obtained from the previous step as input to plot the stock prices. 
   5. The final answer is the plot generated by the 'plot_stock_prices' function. function.

- The plan is passed to the Controller of Coder, the Controller of Coder calls ExtendLibrary.
- The Planner of ExtendLibrary makes the following plan:
  
    Plan:
    1. Write a function named 'plot_stock_prices'. This function should take in a pandas DataFrame as a parameter, which is the output of the 'download_stock_data' function. Inside the function, use matplotlib or any other plotting library to plot the 'Close' prices against the dates. The function should not return anything.

- The Controller of ExtendLibrary calls write_code to write and test the code. Still, we do not provide any more test suites other than checking syntax.
    ```python
    def plot_stock_prices(df):
    """
    Plots the 'Close' prices against the dates.

    Parameters:
    df (pandas.DataFrame): The DataFrame containing the stock data.
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10,5))
    plt.plot(df.index, df['Close'], label='Close Price history') 
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.title('Close Price Trend')
    plt.legend()
    plt.show()
    ```

- The Controller of ExtendLibrary calls save_code to append the function to the code library.
- The Controller of ExtendLibrary calls update_plan to mark the step of plan as done.
- The Controller of ExtendLibrary finishes the flow and resets the flow and its subflows.
- The Controller of Coder calls update_plan to mark the first step of the plan as done.
- The Controller of Coder calls run_code to proceed to the second step of the plan.
  
  ```python
  import importlib
    import library
    importlib.reload(library)
    from library import download_stock_data, plot_stock_prices
  ```
- The Controller calls update_plan to mark the second step of plan as done.
- The Controller calls run_code to proceed the thrid step of the plan.

    ```python
    stock_data = download_stock_data('TSLA', '2022-01-01', '2022-06-01')
    ```
- The Controller of Coder callss run_code to proceed the 4th step of the plan.

    ```python
    plot_stock_prices(stock_data)
    ```
- Plot is generated.
- The Controller of Coder updates the rest of the plan as done.
- The Controller of Coder finishes the CoderFlow, reset the flow and go back to Jarvis.
- The Controller of Jarvis updates the plan to mark the second step of plan as done.
- The Controller of Jarvis calls final_ans to provide the final answer.
- The Controller of Jarvis finishes the Jarvis flow.


### Future Improvements
Due to time constraints, we were not able to refine Jarvis to the very best, here is a list of TODOs:
- When running code tests in [TestCodeFlow](https://huggingface.co/Tachi67/TestCodeFlowModule) we should show the test results to the user and parse for feedback. This can be done by adding a subflow to ask for human feedback (like [this](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/IntermediateAns_Jarvis.py)) to [TestCodeFlow](https://huggingface.co/Tachi67/TestCodeFlowModule/blob/main/TestCodeFlow.py).

- Consider refactoring:
    - Controllers should be generalized:
        - [Controller of JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/Controller_JarvisFlow.py)
        - [Controller of CoderFlow](https://huggingface.co/Tachi67/ExtendLibraryFlowModule/blob/main/ControllerFlow_ExtLib.py)
        - [Controller of ExtendLibraryFlow](https://huggingface.co/Tachi67/CoderFlowModule/blob/main/Controller_CoderFlow.py)
        - [Controller of PlanWriterFlow](https://huggingface.co/Tachi67/PlanWriterFlowModule/blob/main/PlanWriterCtrlFlow.py)
        - [Controller of CodeWriterFlow](https://huggingface.co/Tachi67/CodeWriterFlowModule/blob/main/CodeWriterFlow.py)
    - AskUserFlow should be generalized:
        - [IntermediateAns of JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/IntermediateAns_Jarvis.py)
        - [FinalAns of JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/FinalAns_Jarvis.py)
        - AskUserFlow of each controller
    - Planners should be generalized:
        basically, modify [PlanWriterFlow](https://huggingface.co/Tachi67/PlanWriterFlowModule/tree/main) to make it adapted to:
        - [Planner of JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/Planner_JarvisFlow.py)
        - [Planner of CoderFlow](https://huggingface.co/Tachi67/CoderFlowModule/blob/main/Planner_CoderFlow.py)
    - UpdatePlanFlow should be generalized:
        - [UpdatePlanFlow of JarvisFlow](https://huggingface.co/Tachi67/JarvisFlowModule/blob/main/UpdatePlanAtomicFlow.py)
        - [UpdatePlanFlow of CoderFlow](https://huggingface.co/Tachi67/CoderFlowModule/blob/main/UpdatePlanAtomicFlow.py)
        - [UpdatePlanFlow of ExtendLibraryFlow](https://huggingface.co/Tachi67/ExtendLibraryFlowModule/blob/main/UpdatePlanAtomicFlow.py)
- Clear up prompts to use more examples instead of natural language instructions.
- During the execution of a flow, the user should be press `Crtl + C` to exit the current flow and go back to the caller flow. By doing this, the user should also be able to provide feedback to the controller of the caller flow to instruct what to do next.
- After replanning, the controller sometimes gets confused of the new plan, it may be because that we are simply overriding the plan injected to the system prompts. Consider providing the controller a user message informing it of the new plan (please take notice of the sliding window as it's kind of tricky.)


### Acknowledgement and some nonsense
**WARNING:** This section is not related to the design, implementaion nor usage of Jarvis, the reader can completely skip this section without losing any useful information.

Jarvis is done independently as a semester project by [Haolong Li](https://github.com/Tachi-67) ([haolong.li@epfl.ch](mailto:haolong.li@epfl.ch)) at EPFL, very special and strong thanks to his mentor: Martin Josifoski, and semi-mentor: Nicolas Baldwin (I'm not posting their contacts in case they get mad ;-) ) for their help and support during the design and implementation of Jarvis, love you!

Jarvis is built under the framework of [aiflows](https://github.com/epfl-dlab/aiflows), it's cool -- try it out!

Jarvis is not perfect, December in Switzerland (or EPFL? who knows) sucks, the poor author didn't got the energy to write super clean code, but it runs!! ;) 