from flows.messages import TaskMessage, StateUpdateMessage, OutputMessage, Message


def test_flow_message_init():
    sample_flow_message = StateUpdateMessage(
        message_creator="test-creator", flow_runner="runner", flow_run_id="123", data="Sample content"
    )
    assert isinstance(sample_flow_message, StateUpdateMessage)
    assert sample_flow_message.message_creator == "test-creator"
    assert sample_flow_message.flow_runner == "runner"
    assert sample_flow_message.flow_run_id == "123"
    assert sample_flow_message.data == "Sample content"
    assert sample_flow_message.message_type == "StateUpdateMessage"


def test_flow_update_message_init():
    sample_flow_update_message = StateUpdateMessage(
        message_creator="test-creator", flow_runner="runner", flow_run_id="123", data="Sample content"
    )
    assert isinstance(sample_flow_update_message, StateUpdateMessage)
    assert sample_flow_update_message.message_creator == "test-creator"
    assert sample_flow_update_message.flow_runner == "runner"
    assert sample_flow_update_message.flow_run_id == "123"
    assert sample_flow_update_message.data == "Sample content"
    assert sample_flow_update_message.message_type == "StateUpdateMessage"


def test_task_message_init():
    sample_input_flow_message = TaskMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        output_keys=["exp"],
        data="Sample content",
        target_flow_run_id="target",
    )
    assert isinstance(sample_input_flow_message, TaskMessage)
    assert sample_input_flow_message.message_creator == "test-creator"
    assert sample_input_flow_message.flow_runner == "runner"
    assert sample_input_flow_message.flow_run_id == "123"
    assert sample_input_flow_message.data == "Sample content"
    assert sample_input_flow_message.message_type == "TaskMessage"
    assert sample_input_flow_message.target_flow_run_id == "target"


def test_output_message_init():
    parsed_outputs = {"out-1": 45, "out-2": False}

    sample_output_message = OutputMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        data=parsed_outputs,
        error_message=None,
    )

    assert isinstance(sample_output_message, OutputMessage)
    assert sample_output_message.message_creator == "test-creator"
    assert sample_output_message.flow_runner == "runner"
    assert sample_output_message.flow_run_id == "123"
    assert sample_output_message.data == parsed_outputs
    assert sample_output_message.message_type == "OutputMessage"
    assert not sample_output_message.error_message

    from flows.history import FlowHistory

    assert isinstance(sample_output_message.history, FlowHistory)


def test_init_with_empty_fields():
    sample_flow_message = StateUpdateMessage(
        message_creator="test-creator", flow_runner="runner", data="Sample content"
    )
    assert sample_flow_message.parent_message_ids == []
    assert type(sample_flow_message.message_id) == str
    assert type(sample_flow_message.flow_run_id) == str


def test_uuid():
    message_ids, flow_run_ids = [], []
    n_mess = 20
    for _ in range(n_mess):
        sample_flow_message = Message(message_creator="test-creator", flow_runner="runner", data="Sample content")
        message_ids.append(sample_flow_message.message_id)
        flow_run_ids.append(sample_flow_message.flow_run_id)

    assert len(set(message_ids)) == n_mess
    assert len(set(flow_run_ids)) == n_mess


def test_to_string():
    sample_flow_message = StateUpdateMessage(
        message_creator="test-creator", flow_runner="runner", flow_run_id="123", data="Sample content"
    )

    expected_output_role = f"[{sample_flow_message.message_id} -- 123] test-creator (runner)"
    expected_output_content = "Sample content"
    expected_output_content_dict_keys = [
        "data",
        "created_at",
        "flow_run_id",
        "flow_runner",
        "message_creator",
        "message_id",
        "message_type",
        "parent_message_ids",
    ]

    assert expected_output_role in sample_flow_message.to_string()
    assert expected_output_content in sample_flow_message.to_string()

    dict_str = sample_flow_message.to_string()
    for k in expected_output_content_dict_keys:
        assert k in dict_str


def test_to_dict():
    parsed_outputs = {"out-1": 45, "out-2": False}

    from flows.history import FlowHistory

    history = FlowHistory()
    message1 = Message(message_creator="user1", data="Hello", flow_runner="0")
    message2 = StateUpdateMessage(message_creator="user2", data="Hi", flow_runner="0")
    message3 = Message(message_creator="user1", data="How are you?", flow_runner="0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    sample_output_message = OutputMessage(
        message_creator="test-creator",
        flow_runner="runner",
        flow_run_id="123",
        data=parsed_outputs,
        valid_parsing=True,
        history=history,
    )

    out_dict = sample_output_message.to_dict()

    expected_keys = [
        "data",
        "created_at",
        "flow_run_id",
        "flow_runner",
        "message_creator",
        "message_id",
        "message_type",
        "parent_message_ids",
        "history",
    ]

    for k in expected_keys:
        assert k in out_dict

    assert not out_dict["data"]["out-2"]
    assert out_dict["data"]["out-1"] == 45
    assert len(out_dict["history"]) == 3


def test_deepcopy_content():
    dict_content = {"data": 3, "bool_key": True}

    sample_flow_message = Message(
        message_creator="test-creator", flow_runner="runner", flow_run_id="123", data=dict_content
    )

    dict_content["data"] = 4
    dict_content["bool_key"] = False

    assert sample_flow_message.data["data"] == 3
    assert sample_flow_message.data["bool_key"]


def test_soft_copy():
    dict_content = {"data": 3, "bool_key": True}
    sample_flow_message = Message(
        message_creator="test-creator", flow_runner="runner", flow_run_id="123", data=dict_content
    )

    dict_content["data"] = 4
    dict_content["bool_key"] = False

    new_message = Message(**sample_flow_message.soft_copy())

    sample_flow_message.message_creator = "updated-creator"
    sample_flow_message.data["data"] = 8

    assert new_message.message_creator == "test-creator"
    assert new_message.flow_runner == "runner"
    assert new_message.flow_run_id == "123"
    assert new_message.data["data"] == 3
    assert new_message.data["bool_key"]
    assert new_message.message_id != sample_flow_message.message_id
    assert new_message.created_at != sample_flow_message.created_at
    assert new_message.parent_message_ids == [sample_flow_message.message_id]
