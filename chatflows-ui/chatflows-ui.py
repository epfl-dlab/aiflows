import time
import json
from typing import Dict, Any
import hydra
import queue
from typing import List
import threading

from aiflows.messages import FlowMessage
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils import serve_utils
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.utils.constants import (
    COFLOWS_PATH,
)
from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
)
from aiflows.workers import run_get_instance_worker_thread

import colink as CL
from colink import CoLink
from colink import ProtocolOperator

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.runtime.app_session import AppSession

from shared_objects import shared_queue


def get_streamlit_sessions() -> list[AppSession]:
    runtime: Runtime = Runtime.instance()
    return [s.session for s in runtime._session_mgr.list_sessions()]


def notify() -> None:
    for session in get_streamlit_sessions():
        session._handle_rerun_script_request()


def create_flow(
    config: Dict[str, Any],
    config_overrides: Dict[str, Any] = None,
    state: Dict[str, Any] = None,
):
    if config_overrides is not None:
        config = recursive_dictionary_update(config, config_overrides)

    flow = hydra.utils.instantiate(config, _recursive_=False, _convert_="partial")
    if state is not None:
        flow.__setflowstate__({"flow_state": state}, safe_mode=True)
    print("Created human flow with config:", json.dumps(config, indent=4))
    return flow


def setup_human_flow(cl, flow_endpoint):
    print("Preparing Human Flow and State...")
    cfg = read_yaml_file("HumanUIFlow.yaml")
    proxy = serve_utils.get_flow_instance(
        cl=cl, flow_endpoint=flow_endpoint, config_overrides=cfg
    )
    flow_id = proxy.get_instance_id()
    mount_path = f"{COFLOWS_PATH}:{flow_endpoint}:mounts:local:{flow_id}"
    config_overrides = coflows_deserialize(
        cl.read_entry(f"{mount_path}:config_overrides")
    )
    state = coflows_deserialize(cl.read_entry(f"{mount_path}:state"), use_pickle=True)
    st.session_state["human_flow"] = create_flow(None, config_overrides, state)
    st.session_state["human_flow"].set_colink(cl)

    if state is not None:
        st.session_state["chats"] = state["chats"]

    st.session_state["cl"] = cl
    st.session_state["mount_path"] = mount_path


def save_state_to_colink():
    st.session_state["human_flow"].flow_state["chats"] = st.session_state["chats"]
    new_state = st.session_state["human_flow"].__getstate__()["flow_state"]
    st.session_state["cl"].update_entry(
        f"{st.session_state.mount_path}:state",
        coflows_serialize(new_state, use_pickle=True),
    )


def dispatch_task_handler(cl: CoLink, param: bytes, participants: List[CL.Participant]):
    """
    Receives msgs from dispatch_point and pushes them to shared queue.
    Streamlit thread will then pop this msg from the queue and display it in the UI.
    """
    print("\n~~~ Dispatch task ~~~")
    dispatch_task = coflows_deserialize(param)

    for message_path in dispatch_task["message_ids"]:
        input_msg = FlowMessage.deserialize(cl.read_entry(message_path))
        input_msg.reply_data["input_msg_path"] = message_path
        shared_queue.put(input_msg)
        notify()
        time.sleep(1)


def reload_state():
    try:
        ui_cfg = read_yaml_file("ui-config.yaml")
        cl = CoLink(ui_cfg["colink_address"], ui_cfg["colink_jwt"])
        flow_endpoint = ui_cfg["flow_endpoint"]
    except Exception as e:
        st.error(
            "Configuration file not found or has missing keys.\n"
            "Expecting config at path: ./ui-config.yaml\n\n Error: " + str(e)
        )
        st.stop()

    setup_human_flow(cl, flow_endpoint)


@st.cache_resource
def setup():
    try:
        ui_cfg = read_yaml_file("ui-config.yaml")
        cl = CoLink(ui_cfg["colink_address"], ui_cfg["colink_jwt"])
        flow_endpoint = ui_cfg["flow_endpoint"]
        dispatch_point = ui_cfg["dispatch_point"]
    except Exception as e:
        st.error(
            "Configuration file not found or has missing keys.\n"
            "Expecting config at path: ./ui-config.yaml\n\n Error: " + str(e)
        )
        st.stop()

    serve_utils.serve_flow(
        cl=cl,
        flow_class_name="aiflows.base_flows.AtomicFlow",
        flow_endpoint=flow_endpoint,
        singleton=True,
        dispatch_point=dispatch_point,
    )
    setup_human_flow(cl, flow_endpoint)

    pop = ProtocolOperator(__name__)

    proto_role = "human_dispatch:local"
    pop.mapping[proto_role] = dispatch_task_handler

    thread = threading.Thread(target=pop.run, args=(cl, True, None, True), daemon=True)
    thread.start()
    print("Dispatch worker started in attached thread.")
    run_get_instance_worker_thread(cl)
    print("get_instance worker started in attached thread.")


def handle_msg(msg):
    chat_id = f"{msg.user_id}:{msg.src_flow_id}"
    print(f"Received msg in chat {chat_id}.")

    if chat_id not in st.session_state["chats"]:
        st.session_state["chats"][chat_id] = {}
        st.session_state["chats"][chat_id]["chat_label"] = msg.src_flow
        st.session_state["chats"][chat_id]["messages"] = []

    msg_content = msg.data["query"]
    st.session_state["chats"][chat_id]["messages"].append(
        {"role": "assistant", "content": msg_content}
    )
    st.session_state["chats"][chat_id]["last_assistant_msg"] = msg

    save_state_to_colink()

    if "current_chat_id" not in st.session_state:
        set_current_chat(chat_id)

    if st.session_state["current_chat_id"] != chat_id:
        st.info(f"Received new message from {msg.src_flow}")


def set_current_chat(chat_id):
    st.session_state["current_chat_id"] = chat_id
    print("set current chat id to", chat_id)


def poll_shared_queue():
    try:
        msg = shared_queue.get_nowait()
        handle_msg(msg)
    except queue.Empty:
        pass


def display_current_chat():
    if "current_chat_id" not in st.session_state:
        return

    current_chat_id = st.session_state["current_chat_id"]
    messages = st.session_state["chats"][current_chat_id]["messages"]
    chat_label = st.session_state["chats"][current_chat_id]["chat_label"]

    st.title(f"💬 {chat_label}")
    st.caption(current_chat_id)
    for msg in messages:
        st.chat_message(msg["role"]).write(msg["content"])


# STREAMLIT SCRIPT

st.markdown(
    """
    <style>
    button {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

setup()

if "human_flow" not in st.session_state:
    reload_state()

if "chats" not in st.session_state:
    st.session_state["chats"] = {}

poll_shared_queue()

with st.sidebar:
    st.title("💬 ChatFlows")
    st.caption("🚀  Chat with your Flows.")

    for chat_id, chat in st.session_state["chats"].items():
        if st.button(chat["chat_label"], key=chat_id):
            set_current_chat(chat_id)

display_current_chat()

if human_input := st.chat_input("What is up?"):
    st.chat_message("user").write(human_input)

    if "current_chat_id" in st.session_state:
        current_chat_id = st.session_state["current_chat_id"]
        last_assistant_msg = st.session_state["chats"][current_chat_id][
            "last_assistant_msg"
        ]

        reply_message = st.session_state["human_flow"].package_output_message(
            input_message=last_assistant_msg,
            response={"human_input": human_input},
        )

        print("Sending msg in chat_id", st.session_state["current_chat_id"])
        st.session_state["human_flow"].send_message(reply_message)

        st.session_state["chats"][current_chat_id]["messages"].append(
            {"role": "user", "content": human_input}
        )

        save_state_to_colink()
