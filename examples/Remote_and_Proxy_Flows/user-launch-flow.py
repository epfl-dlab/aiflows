import logging
import colink as CL
from colink import CoLink, decode_jwt_without_validation, byte_to_str

from aiflows.utils.general_helpers import read_yaml_file

import os
import pickle
from omegaconf import OmegaConf

if __name__ == "__main__":
    logging.basicConfig(
        filename="user-launch-flow.log", filemode="a", level=logging.INFO
    )

    with open("jwts.txt", "r") as user_jwts:
        jwt_a = user_jwts.readline().rstrip()
        jwt_b = user_jwts.readline().rstrip()

    user_id_a = decode_jwt_without_validation(jwt_a).user_id
    user_id_b = decode_jwt_without_validation(jwt_b).user_id

    participants = [
        CL.Participant(
            user_id=user_id_a,
            role="flow-initiator",
        ),
        CL.Participant(
            user_id=user_id_b,
            role="flow-server",
        ),
    ]

    # user a connects to server
    addr = "http://127.0.0.1:2021"
    cl = CoLink(addr, jwt_a)

    # Start task
    print("starting task...")
    task_id = cl.run_task("flow-protocol", 2, participants, False)
    print("Created task with id", task_id)

    # input data
    data = {"id": 0, "number": 1235}
    user_input_bytes = pickle.dumps(data)

    # Write input data to private storage
    print("Writing input data to storage")
    cl.create_entry("tasks:{}:user_input".format(task_id), user_input_bytes)

    # Read config
    root_dir = "."
    cfg_path = os.path.join(root_dir, "sequential_proxy.yaml")
    with open(cfg_path, "r") as f:
        cfg = OmegaConf.load(f)
    cfg = read_yaml_file(cfg_path)

    # Write config to private storage
    print("Writing cfg to storage")
    cfg_bytes = pickle.dumps(cfg)
    cl.create_entry("tasks:{}:flow_cfg".format(task_id), cfg_bytes)

    # Read output from storage
    print("waiting for result...")
    res_bytes = cl.read_or_wait(f"tasks:{task_id}:output")
    res = pickle.loads(res_bytes)
    print(f"result: {res}")

    # Wait for task to finish
    cl.wait_task(task_id)
    print(f"task finished: {task_id}")
