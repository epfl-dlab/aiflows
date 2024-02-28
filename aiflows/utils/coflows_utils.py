from typing import Any
import uuid
import json
import colink as CL
import pickle

PUSH_ARGS_TRANSFER_PATH = "push_tasks"


class FlowFuture:
    def __init__(self, cl, msg_id):
        self.cl = cl
        self.colink_storage_key = f"{PUSH_ARGS_TRANSFER_PATH}:{msg_id}:response"

    def try_get(self):
        """
        Non-blocking read, returns None if there is no response yet.
        """
        return pickle.loads(self.cl.read_entry(self.colink_storage_key))

    def get(self, output_data_only=True):
        """
        Blocking read, creates colink queue in background and subscribes to it.
        Probably shouldn't create queue and should have timeout.
        """
        
        message = pickle.loads(self.cl.read_or_wait(self.colink_storage_key))
        
        if output_data_only:
            return message.data["output_data"]
        
        return message


def push_to_flow(cl, target_user_id, target_flow_ref, message):
    if target_user_id == "local" or target_user_id == cl.get_user_id():
        participants = [
            CL.Participant(
                user_id=cl.get_user_id(),
                role="receiver",
            ),
        ]
    else:
        participants = [
            CL.Participant(
                user_id=cl.get_user_id(),
                role="initiator",
            ),
            CL.Participant(
                user_id=target_user_id,
                role="receiver",
            ),
        ]

    push_msg_id = uuid.uuid4()
    cl.create_entry(
        f"{PUSH_ARGS_TRANSFER_PATH}:{push_msg_id}:msg",
        pickle.dumps(message),
    )

    push_param = {
        "flow_id": target_flow_ref,
        "message_id": str(push_msg_id),
    }
    cl.run_task("coflows_push", coflows_serialize(push_param), participants, True)
    return push_msg_id

def coflows_serialize(data: Any) -> bytes:
    json_str = json.dumps(data)
    return json_str.encode("utf-8")


def coflows_deserialize(encoded_data: bytes) -> Any:
    if encoded_data is None:
        return None
    json_str = encoded_data.decode("utf-8")
    return json.loads(json_str)
