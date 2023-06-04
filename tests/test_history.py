from src.history import History, FlowHistory
from src.messages import FlowMessage
import pytest


def test_empty_history() -> None:
    history = FlowHistory()
    assert len(history) == 0


def test_add_message() -> None:
    history = FlowHistory()
    message = FlowMessage(message_creator="user", content="Hello", flow_runner="0")
    history.add_message(message)
    assert len(history) == 1


def test_get_messages_by() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0")
    message3 = FlowMessage(message_creator="user1", content="How are you?", flow_runner="0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    messages = history.get_messages_by("user1")
    assert len(messages) == 2
    assert messages[0] == message1
    assert messages[1] == message3


def test_to_string() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="flow_run_0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    output_str = history.to_string()
    assert "user1" in output_str
    assert "user2" in output_str
    assert "Hello" in output_str
    assert "Hi" in output_str
    assert "flow_run_0" in output_str
    assert len(str(history).split("\n")) >= 2


def test_to_dict() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="flow_run_0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    dd = history.to_dict()

    expected_keys = ["message_id", "created_at", "message_type",
                     "parents", "flow_run_id", "message_index",
                     "message_creator", "content", "flow_runner"]

    assert "history" in dd
    for exp_k in expected_keys:
        assert exp_k in dd["history"][0]
        assert exp_k in dd["history"][1]
    assert dd["history"][0]["message_creator"] == "user1"
    assert dd["history"][1]["message_creator"] == "user2"


def test_remove_messages() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="flow_run_0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    to_remove = [message1.message_id]
    history.remove_messages(to_remove)

    assert len(history) == 1

    with pytest.raises(Exception):
        history.remove_messages(to_remove)

    to_remove = [message2.message_id]
    history.remove_messages(to_remove)

    assert len(history) == 0
    with pytest.raises(Exception):
        history.remove_messages(to_remove)


def test_get_latest_message() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="flow_run_0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)

    assert history.get_latest_message().message_creator == "user2"
    to_remove = [history.get_latest_message().message_id]
    history.remove_messages(to_remove)

    assert history.get_latest_message().message_creator == "user1"
    to_remove = [history.get_latest_message().message_id]
    history.remove_messages(to_remove)

    assert history.get_latest_message() is None


def test_deepcopy_str() -> None:
    history_a = History()
    history_b = FlowHistory()

    original_content = "Original Information"
    original_creator = "test"
    message = FlowMessage(content=original_content, message_creator=original_creator, flow_runner="flow_run_0")

    # ~~~ Test behavior for history_a ~~~
    history_a.add_message(message)

    modified_content = "Modified"
    message.content = modified_content

    assert len(history_a) == 1
    assert history_a.messages[0].content == original_content

    # ~~~ Test behavior for history_b ~~~
    history_b.add_message(message)
    modified_creator = "modifier"
    message.message_creator = modified_creator

    assert len(history_b) == 1
    assert history_b.messages[0].content == modified_content
    assert history_b.messages[0].message_creator == original_creator


def test_deepcopy_other_data() -> None:
    history_a = History()
    history_b = FlowHistory()

    # ~~~ Preparations ~~~
    original_content = "Original Information"
    original_creator = "test"
    message = FlowMessage(content=original_content, message_creator=original_creator, flow_runner="flow_run_0")
    history_a.add_message(message)

    original_content = {"data": "Original Information", "bool": True, "history": history_a}
    original_creator = "test"
    new_message = FlowMessage(content=original_content, message_creator=original_creator, flow_runner="flow_run_0")
    history_b.add_message(new_message)

    # ~~~ Perturbate ~~~
    modified_creator = "modified-creator"
    new_message.content["bool"] = False
    new_message.content["history"].messages[0].content = modified_creator

    # ~~~ Test ~~~
    assert len(history_b) == 1
    assert history_b.messages[-1].content["bool"]
    assert history_b.messages[-1].content["history"].messages[0].content == history_a.messages[0].content


def test_flow_run_ids():
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="0", flow_run_id="flow_run_0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0", flow_run_id="flow_run_1")
    message3 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0", flow_run_id="flow_run_0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    assert history.flow_run_ids == {"flow_run_0", "flow_run_1"}


def test_flow_run_ids_random() -> None:
    history = FlowHistory()
    message1 = FlowMessage(message_creator="user1", content="Hello", flow_runner="0")
    message2 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0")
    message3 = FlowMessage(message_creator="user2", content="Hi", flow_runner="0")

    history.add_message(message1)
    history.add_message(message2)
    history.add_message(message3)

    assert len(history.flow_run_ids) == 3
