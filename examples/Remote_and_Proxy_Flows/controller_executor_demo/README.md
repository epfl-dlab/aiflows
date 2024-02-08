## Running Controller Executor Demoe

### Start a server
Example script:
```bash
./colink-server --address 0.0.0.0 --port 2021 --core-u
```

### Exchange JWTS and create users
1. The server you just started have created a `host_token.txt` file in the current directory. Copy and paste it in `reverse_number/user_exchange.py` to the `core_jwt` variable:
    ```python
    core_jwt = #Paste the token in host_token.txt here
    ```

2. In a new shell, run the `user_exchange.py` script:
    ```bash
    conda activate coflows
    cd examples/Remote_and_Proxy_Flows/
    python user_exchange.py
    ```

3. This will print out 2 `user_jwt` tokens. Copy and paste the token of `user 1` in all the `remote_participant_id` fields of the following files:
-  `examples/Remote_and_Proxy_Flows/controller_executor_demo/proxy_circular.yaml`
- `examples/Remote_and_Proxy_Flows/controller_executor_demo/controller_executor_flow_ephemeral.yaml``


4. Copy and pase the second jwt token of `examples/Remote_and_Proxy_Flows/jwts.txt` to the `jwt`field of the following files:
    - `examples/Remote_and_Proxy_Flows/controller_executor_demo/controller_executor_flow_ephemeral.yaml`
    - `examples/Remote_and_Proxy_Flows/controller_executor_demo/serve_controller.yaml`
    - `examples/Remote_and_Proxy_Flows/controller_executor_demo/serve_executor.yaml`

5. Copy and pase the first jwt token of `examples/Remote_and_Proxy_Flows/jwts.txt` to the `jwt`field of the following files:
    - `examples/Remote_and_Proxy_Flows/controller_executor_demo/proxy_circular.yaml``

### Start The Permanent Flows and Flow Operators

1. Open a new terminal and start serving executor permanent flow:
    ```bash
    conda activate coflows
    pip install wikipedia
    cd examples/Remote_and_Proxy_Flows/controller_executor_demo
    python serve_executor.py
    ```
2. Open a new terminal and start serving controller permanent flow:
    ```bash
    conda activate coflows
    cd examples/Remote_and_Proxy_Flows/controller_executor_demo
    python serve_controller.py
    ```
3. Open a new terminal and start the worker node for user 0:
    ```bash
    conda activate coflows
    cd examples/Remote_and_Proxy_Flows/controller_executor_demo
    python user0_worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ../jwts.txt) --vt-public-addr 127.0.0.1
    ```
4. openn a new terminal and start the worker node for user 1 enabling ephemeral flows of our Controller Executor:
    ```bash
    conda activate coflows
    cd examples/Remote_and_Proxy_Flows/controller_executor_demo
    python controller_executor_flow_ephemeral.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ../jwts.txt) --vt-public-addr 127.0.0.1
    ````

### Start The Proxy Circular Flow

Open a new terminal and start the proxy circular flow:
```bash
conda activate coflows
cd examples/Remote_and_Proxy_Flows/controller_executor_demo
python proxy_circular.py
````
