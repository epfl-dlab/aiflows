# ChatAtomicFlow

## Definition

The `ChatAtomicFlow` is a flow that seamlessly interfaces with an LLM through an API, generating textual responses for textual inputs. Powered by the LiteLLM library in the backend, `ChatAtomicFlow` supports various API providers; explore the full list [here](https://docs.litellm.ai/docs/providers). For a detailed understanding of its parameters, refer to its [`FlowCard`](https://huggingface.co/aiflows/VectorStoreFlowModule) for an extensive description of its parameters.

## Methods


In this section, we'll explore some o `ChatAtomicFlow`'s methods, specifically those invoked when it is called.

Just like every flow, `ChatAtomicFlow` is called via the `run` method:

```python
def run(self,input_data: Dict[str, Any]):
        """ This method runs the flow. It processes the input, calls the backend and updates the state of the flow.
        
        :param input_data: The input data of the flow.
        :type input_data: Dict[str, Any]
        :return: The LLM's api output.
        :rtype: Dict[str, Any]
        """
        
        # ~~~ Process input ~~~
        self._process_input(input_data)

        # ~~~ Call ~~~
        response = self._call()
        
        #loop is in case there was more than one answer (n>1 in generation parameters)
        for answer in response:
            self._state_update_add_chat_message(
                role=self.flow_config["assistant_name"],
                content=answer
            )
        response = response if len(response) > 1 or len(response) == 0 else response[0]
        return {"api_output": response}
```

As you can see in the code snippet here above, `run` processes the input data of the flow via the `_process_input` method. Let's take a closer look at what it does:


```python
def _process_input(self, input_data: Dict[str, Any]):
        """ This method processes the input of the flow. It adds the human message to the flow's state. If the conversation is not initialized, it also initializes it
        (adding the system message and potentially the demonstrations).
        
        :param input_data: The input data of the flow.
        :type input_data: Dict[str, Any]
        """
        if self._is_conversation_initialized():
            # Construct the message using the human message prompt template
            user_message_content = self._get_message(self.human_message_prompt_template, input_data)

        else:
            # Initialize the conversation (add the system message, and potentially the demonstrations)
            self._initialize_conversation(input_data)
            if getattr(self, "init_human_message_prompt_template", None) is not None:
                # Construct the message using the query message prompt template
                user_message_content = self._get_message(self.init_human_message_prompt_template, input_data)
            else:
                user_message_content = self._get_message(self.human_message_prompt_template, input_data)

        self._state_update_add_chat_message(role=self.flow_config["user_name"],
                                            content=user_message_content)
```
This function prepares the user message prompt for submission to the Language Model (LLM) by inserting the `input_data` into the placeholders of the user prompt template (details of which will be explained later). The choice of user prompt sent to the LLM depends on whether the conversation has been initiated or not (i.e., whether the flow has been called):

- If the conversation has not been initialized, the message is constructed using the `init_human_message_prompt_template`. In this case, the expected input interface for the flow is specified by `input_interface_non_initialized`.

- If the conversation has been initialized, the message is constructed using the `human_message_prompt_template`. In this case, the expected input interface for the flow is specified by `input_interface_initialized`.

This distinction proves useful when different inputs are needed for the initial query compared to subsequent queries to the flow. For example, in ReAct, the first query to the LLM is initiated by a human, such as asking a question. In subsequent queries, the input is derived from the execution of a tool (e.g., a query to Wikipedia). In ReAct's implementation, these two scenarios are differentiated by ChatAtomicFlow's `input_interface_non_initialized` and `input_interface_initialized`, which define the input interface for the flow.

[ChatAtomicFlow's default configuration](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.yaml) defines user prompt templates as so:
```yaml
init_human_message_prompt_template:
  _target_: aiflows.prompt_template.JinjaPrompt

human_message_prompt_template:
  _target_: aiflows.prompt_template.JinjaPrompt
  template: "{{query}}"
  input_variables:
    - "query"
input_interface_initialized:
  - "query"
```
This signifies that `init_human_message_prompt_template` represents an empty string message, while the rendered message for `human_message_prompt_template` is derived from the previous flow's query. This is achieved by placing the input variable "query" (from `input_dict`) into the `{{query}}` placeholder of the prompt template.

Finally, the `run` function calls the LLM via the LiteLLM library, saves the message in it's flow state and sends the output to the next flow.

**Additional Documentation:**

* To delve into the extensive documentation for `ChatAtomicFlow`, refer to its [FlowCard on the FlowVerse](https://huggingface.co/aiflows/ChatFlowModule)
* Find `ChatAtomicFlow`'s default [configuration here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.yaml)