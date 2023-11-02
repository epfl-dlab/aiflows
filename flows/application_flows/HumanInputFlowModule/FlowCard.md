Reads input from the user's standard input source.

## Parameters

request_multi_line_input_flag (Boolean): If true, the user will be prompted to enter multiple lines of input. If false, the user will be prompted to enter a single line of input.

query_message_prompt_template (Dict):
    template (String): The template for the message to be presented to the user (e.g., "The last `{{action}}` completed successfully. Do you have any feedback that should be considered before selecting the next action?"). Default value is "".
    input_variables (List): The list of variables to be used in the template (e.g., ["action"]). Default value is [].

input_keys (List): The list of input keys that should be passed to the Flow as input. Default value is [].

## Input

By default, this Flow does not expect any input.

## Output

human_input (String): The user's input.