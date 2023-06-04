from src.messages import FlowUpdateMessage, FlowMessage, InputMessage, OutputMessage


def test_flow_message_init():
    sample_flow_message = FlowMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content"
    )
    assert isinstance(sample_flow_message, FlowMessage)
    assert sample_flow_message.message_creator == "test-creator"
    assert sample_flow_message.flow_runner == "runner"
    assert sample_flow_message.flow_run_id == "123"
    assert sample_flow_message.content == "Sample content"
    assert sample_flow_message.message_type == "flow-message"


def test_flow_update_message_init():
    sample_flow_update_message = FlowUpdateMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content"
    )
    assert isinstance(sample_flow_update_message, FlowUpdateMessage)
    assert sample_flow_update_message.message_creator == "test-creator"
    assert sample_flow_update_message.flow_runner == "runner"
    assert sample_flow_update_message.flow_run_id == "123"
    assert sample_flow_update_message.content == "Sample content"
    assert sample_flow_update_message.message_type == "flow-update-message"


def test_input_message_init():
    inputs = {"in-1": FlowMessage(
        message_creator="input-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=45,
    ), "in-2": FlowMessage(
        message_creator="input-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=False,
    )}
    sample_input_flow_message = InputMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content",
        inputs=inputs,
        target_flow="target"
    )
    assert isinstance(sample_input_flow_message, InputMessage)
    assert sample_input_flow_message.message_creator == "test-creator"
    assert sample_input_flow_message.flow_runner == "runner"
    assert sample_input_flow_message.flow_run_id == "123"
    assert sample_input_flow_message.content == "Sample content"
    assert sample_input_flow_message.message_type == "input-message"
    assert sample_input_flow_message.target_flow == "target"
    assert len(sample_input_flow_message.inputs) == 2


def test_output_message_init():
    parsed_outputs = {"out-1": FlowMessage(
        message_creator="output-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=45,
    ), "out-2": FlowMessage(
        message_creator="output-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=False,
    )}

    sample_output_message = OutputMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content",
        parsed_outputs=parsed_outputs,
        valid_parsing=False,
        target_flow="target"
    )

    assert isinstance(sample_output_message, OutputMessage)
    assert sample_output_message.message_creator == "test-creator"
    assert sample_output_message.flow_runner == "runner"
    assert sample_output_message.flow_run_id == "123"
    assert sample_output_message.content == "Sample content"
    assert sample_output_message.message_type == "output-message"
    assert not sample_output_message.valid_parsing
    assert len(sample_output_message.parsed_outputs) == 2

    from src.history import FlowHistory
    assert isinstance(sample_output_message.message_creation_history, FlowHistory)


def test_init_with_empty_fields():
    sample_flow_message = FlowMessage(
        message_creator="test-creator",
        flow_runner="runner",
        content="Sample content"
    )
    assert sample_flow_message.parents == []
    assert type(sample_flow_message.message_id) == str
    assert type(sample_flow_message.flow_run_id) == str


def test_uuid():
    message_ids, flow_run_ids = [], []
    n_mess = 20
    for _ in range(n_mess):
        sample_flow_message = FlowMessage(
            message_creator="test-creator",
            flow_runner="runner",
            content="Sample content"
        )
        message_ids.append(sample_flow_message.message_id)
        flow_run_ids.append(sample_flow_message.flow_run_id)

    assert len(set(message_ids)) == n_mess
    assert len(set(flow_run_ids)) == n_mess


def test_to_string():
    sample_flow_message = FlowMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content"
    )

    expected_output_role = f"[{sample_flow_message.message_id} -- 123] test-creator (runner)"
    expected_output_content = "Sample content"
    expected_output_content_dict_keys = ["content", "created_at", "flow_run_id", "flow_runner",
                                         "message_creator", "message_id", "message_index",
                                         "message_type", "parents"]

    assert expected_output_role in sample_flow_message.to_string()
    assert expected_output_content in sample_flow_message.to_string()

    dict_str = sample_flow_message.to_string(show_dict=True)
    for k in expected_output_content_dict_keys:
        assert k in dict_str


def test_to_dict():
    parsed_outputs = {"out-1": FlowMessage(
        message_creator="output-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=45,
    ), "out-2": FlowMessage(
        message_creator="output-creator",
        flow_runner="launcher",
        flow_run_id="00",
        content=False,
    )}

    from src.history import FlowHistory
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0")
    message3 = FlowMessage(message_creator="user1", content="How are you?", flow_runner="0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    sample_output_message = OutputMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content="Sample content",
        parsed_outputs=parsed_outputs,
        valid_parsing=True,
        target_flow="target",
        message_creation_history=history
    )

    out_dict = sample_output_message.to_dict()

    expected_keys = ["content", "created_at", "flow_run_id", "flow_runner",
                     "message_creator", "message_id", "message_index",
                     "message_type", "parents",
                     "parsed_outputs", "message_creation_history"]

    for k in expected_keys:
        assert k in out_dict

    assert not out_dict["parsed_outputs"]["out-2"]["content"]
    assert out_dict["parsed_outputs"]["out-1"]["content"] == 45
    assert len(out_dict["message_creation_history"]["history"]) == 3


def test_deepcopy_content():
    dict_content = {"data": 3, "bool_key": True}

    sample_flow_message = FlowMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content=dict_content
    )

    dict_content["data"] = 4
    dict_content["bool_key"] = False

    assert sample_flow_message.content["data"] == 3
    assert sample_flow_message.content["bool_key"]


def test_soft_copy():
    dict_content = {"data": 3, "bool_key": True}
    sample_flow_message = FlowMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        content=dict_content
    )

    dict_content["data"] = 4
    dict_content["bool_key"] = False

    new_message = FlowMessage(**sample_flow_message.soft_copy())

    sample_flow_message.message_creator = "updated-creator"
    sample_flow_message.content["data"] = 8

    assert new_message.message_creator == "test-creator"
    assert new_message.flow_runner == "runner"
    assert new_message.flow_run_id == "123"
    assert new_message.content["data"] == 3
    assert new_message.content["bool_key"]
    assert new_message.message_id != sample_flow_message.message_id
    assert new_message.created_at != sample_flow_message.created_at
    assert new_message.message_index > sample_flow_message.message_index
    assert new_message.parents == [sample_flow_message.message_id]
