import colink as CL
import pickle
from typing import List


def get_next_update_message(subscriber):
    message = CL.SubscriptionMessage().FromString(
        subscriber.get_next()
    )

    while message.change_type != "update":
        message = CL.SubscriptionMessage().FromString(
            subscriber.get_next()
        )

    return pickle.loads(message.payload)


def create_subscriber(cl,response_queue_name):
    response_queue = cl.subscribe(response_queue_name, None)
                
    return cl.new_subscriber(response_queue)


# def get_simple_ephemeral_flow_protocol(cl: CL.CoLink, param: bytes, participants:  List[CL.Participant]):
#     print("\n~~~ simple-ephemeral-flow:initiator task_id =", cl.get_task_id(), "~~~")
#     if len(participants) > 2:
#         print(
#             "Warning: simple-ephemeral-flow protocol expects two participants: initiator and target. Current task has",
#             len(participants),
#             "participants",
#         )
    
#     target_flow_queue = pickle.loads(param)
#     print("Target flow queue:", target_flow_queue)
#     # ~~~ Get input from task starter ~~~
#     print("Received input from task starter...")
#     input_msg = cl.read_or_wait(
#         f"simple-ephemeral-flow-init:{target_flow_queue}:{cl.get_task_id()}:input_msg",
#     )
    
#     #assuming that message contains state and flow_config
#     input_msg = pickle.loads(input_msg)
    
#     #get meta data (contains state and flow_config)
#     colink_meta_data = input_msg.data.pop("colink_meta_data")
#     state = colink_meta_data["state"]
#     flow_config = colink_meta_data["flow_config"]
    
#     # Make sure colink info is included in config (if not, use default colink info).
#     # It's usally not included in the input message (colink info of proxy flow is not same as local flow)
#     if "colink_info" not in flow_config:
#         default_colink_info = Flow.__default_flow_config["colink_info"] #makes the flow local
#         flow_config["colink_info"] = default_colink_info
        
#     flow = hydra.utils.instantiate(flow_config)
#     flow.__setflowstate__(state, safe_mode=True)

#     #run the flow
#     output_msg = flow.run(input_msg.data)
    
#     # ~~~ Invoke target-flow protocol operator ~~~
#     print("Invoking target-flow worker...")
#     cl.send_variable("input_msg", output_msg, [participants[1]])
#     output_msg_b = cl.recv_variable("output_msg", participants[1])

#     # ~~~ Return output to task starter ~~~
#     print("Relaying output to task starter...")
#     cl.create_entry(
#         f"simple-ephemeral-flow-init:{target_flow_queue}:{cl.get_task_id()}:output_msg",
#         output_msg_b,
#     )
    
    