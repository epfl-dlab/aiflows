# Vision Atomic Flow
**Prequisite**: [Chat Atomic Flow](./chat_flow.md)

## Definition

The `VisionAtomicFlow` is a flow that seamlessly interfaces with an LLM through an API, . It is a flow that, given a textual input, and a set of images and/or videos, generates a textual output. Powered by the LiteLLM library in the backend, `VisionAtomicFlow` supports various API providers; explore the full list [here](https://docs.litellm.ai/docs/providers). For a detailed understanding of its parameters, refer to its [`FlowCard`](https://huggingface.co/aiflows/VisionFlowModule) for an extensive description of its parameters.

## Methods

In this section, we'll delve into some of the methods within the `VisionAtomicFlow` class, specifically those invoked when it is called.

If you examine the [`VisionAtomicFlow` class](https://huggingface.co/aiflows/VisionFlowModule/blob/main/VisionAtomicFlow.py), you'll observe the following:

1. It's a class that inherits from the `ChatAtomicFlow`.
2. There is no `run` method explicitly defined, and as a result, it shares the same `run` method as `ChatAtomicFlow`, which is the method always called when a flow is invoked.

Here is the run method of VisionAtomicFlow:
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

In the provided code snippet, observe that the `run` method handles the input data of the flow through the `_process_input` method. Let's delve into a closer examination of its functionality:


```python
def _process_input(self, input_data: Dict[str, Any]):
        """ This method processes the input data (prepares the messages to send to the API).
        
        :param input_data: The input data.
        :type input_data: Dict[str, Any]
        :return: The processed input data.
        :rtype: Dict[str, Any]
        """
        if self._is_conversation_initialized():
            # Construct the message using the human message prompt template
            user_message_content = self.get_user_message(self.human_message_prompt_template, input_data)

        else:
            # Initialize the conversation (add the system message, and potentially the demonstrations)
            self._initialize_conversation(input_data)
            if getattr(self, "init_human_message_prompt_template", None) is not None:
                # Construct the message using the query message prompt template
                user_message_content = self.get_user_message(self.init_human_message_prompt_template, input_data)
            else:
                user_message_content = self.get_user_message(self.human_message_prompt_template, input_data)

        self._state_update_add_chat_message(role=self.flow_config["user_name"],
                                            content=user_message_content)
```


When calling `_process_input(input_data)` in `VisionAtomicFlow`, the flow generates its user message prompt similarly to `ChatAtomicFlow` (refer to [ChatAtomicFlow's detailed example](./chat_flow.md)). However, due to a slight modification in the `get_user_message` method compared to `ChatAtomicFlow`, it also includes one or multiple images or videos in the input.

```python
 @staticmethod
    def get_user_message(prompt_template, input_data: Dict[str, Any]):
        """ This method constructs the user message to be passed to the API.
        
        :param prompt_template: The prompt template to use.
        :type prompt_template: PromptTemplate
        :param input_data: The input data.
        :type input_data: Dict[str, Any]
        :return: The constructed user message (images , videos and text).
        :rtype: Dict[str, Any]
        """
        content = VisionAtomicFlow._get_message(prompt_template=prompt_template,input_data=input_data)
        media_data = input_data["data"]
        if "video" in media_data:
            content = [ content[0], *VisionAtomicFlow.get_video(media_data["video"])]
        if "images" in media_data:
            images = [VisionAtomicFlow.get_image(image) for image in media_data["images"]]
            content.extend(images)
        return content
```

Note that images can be passed either via a URL (an image on the internet) or by providing the path to a local image. However, videos must be local videos.


Finally, the `run` function calls the LLM via the LiteLLM library, saves the message in it's flow state and sends the textual output to the next flow.

**Additional Documentation:**

* To delve into the extensive documentation for `VisionAtomicFlow`, refer to its [FlowCard on the FlowVerse](https://huggingface.co/aiflows/VisionFlowModule)
* Find `ChatAtomicFlow`'s default [configuration here](https://huggingface.co/aiflows/VisionFlowModule/blob/main/demo.yaml)