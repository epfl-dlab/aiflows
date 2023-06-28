from flows.history import FlowHistory
from flows.messages import Message
import pytest


def test_empty_history() -> None:
    history = FlowHistory()
    assert len(history) == 0


def test_add_message() -> None:
    history = FlowHistory()
    message = Message(message_creator="user", data="Hello", flow_runner="0")
    history.add_message(message)
    assert len(history) == 1


def test_get_messages_by() -> None:
    history = FlowHistory()
    message1 = Message(message_creator="user1", data="Hello", flow_runner="0")
    message2 = Message(message_creator="user2", data="Hi", flow_runner="0")
    message3 = Message(message_creator="user1", data="How are you?", flow_runner="0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    messages = history.get_messages_by("user1")
    assert len(messages) == 2
    assert messages[0] == message1
    assert messages[1] == message3


def test_to_string() -> None:
    history = FlowHistory()
    message1 = Message(message_creator="user1", data="Hello", flow_runner="flow_run_0")
    message2 = Message(message_creator="user2", data="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    output_str = history.to_string()
    assert "user1" in output_str
    assert "user2" in output_str
    assert "Hello" in output_str
    assert "Hi" in output_str
    assert "flow_run_0" in output_str
    assert len(str(history).split("\n")) >= 2


def test_to_list() -> None:
    history = FlowHistory()
    message1 = Message(message_creator="user1", data="Hello", flow_runner="flow_run_0")
    message2 = Message(message_creator="user2", data="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    dd = history.to_list()

    expected_keys = ["message_id", "created_at", "message_type",
                     "parent_message_ids", "flow_run_id",
                     "message_creator", "data", "flow_runner"]

    for exp_k in expected_keys:
        assert exp_k in dd[0]
        assert exp_k in dd[1]
    assert dd[0]["message_creator"] == "user1"
    assert dd[1]["message_creator"] == "user2"


def test_get_latest_message() -> None:
    history = FlowHistory()
    message1 = Message(message_creator="user1", data="Hello", flow_runner="flow_run_0")
    message2 = Message(message_creator="user2", data="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    assert history.get_latest_message().message_creator == "user2"

    history.add_message(message1)
    assert history.get_latest_message().message_creator == "user1"


def test_deepcopy_str() -> None:
    history_a = FlowHistory()
    history_b = FlowHistory()

    original_content = "Original Information"
    original_creator = "test"
    message = Message(data=original_content, message_creator=original_creator, flow_runner="flow_run_0")

    # ~~~ Test behavior for history_a ~~~
    history_a.add_message(message)

    modified_content = "Modified"
    message.data = modified_content

    assert len(history_a) == 1
    assert history_a.messages[0].data == original_content

    # ~~~ Test behavior for history_b ~~~
    history_b.add_message(message)
    modified_creator = "modifier"
    message.message_creator = modified_creator

    assert len(history_b) == 1
    assert history_b.messages[0].data == modified_content
    assert history_b.messages[0].message_creator == original_creator


def test_deepcopy_other_data() -> None:
    history_a = FlowHistory()
    history_b = FlowHistory()

    # ~~~ Preparations ~~~
    original_content = "Original Information"
    original_creator = "test"
    message = Message(data=original_content, message_creator=original_creator, flow_runner="flow_run_0")
    history_a.add_message(message)

    original_content = {"data": "Original Information", "bool": True, "history": history_a}
    original_creator = "test"
    new_message = Message(data=original_content, message_creator=original_creator, flow_runner="flow_run_0")
    history_b.add_message(new_message)

    # ~~~ Perturbate ~~~
    modified_creator = "modified-creator"
    new_message.data["bool"] = False
    new_message.data["history"].messages[0].content = modified_creator

    # ~~~ Test ~~~
    assert len(history_b) == 1
    assert history_b.messages[-1].data["bool"]
    assert history_b.messages[-1].data["history"].messages[0].data == history_a.messages[0].data
