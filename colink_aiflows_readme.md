## Installation
```bash
conda create -n coflows python=3.11
conda activate coflows
pip install -e .
pip install colink
```
## Start a server (tested on MacOS)

### Installations to start a server
Useful link: https://co-learn.notion.site/Run-data-collaborations-with-decentralized-programming-9617651a8224485a9d2916aa366b57b3

```bash
mkdir colink-server && cd colink-server
wget https://github.com/CoLearn-Dev/colink-server-dev/releases/download/v0.3.3/colink-server-macos-x86_64.tar.gz && tar -zxvf colink-server-macos-x86_64.tar.gz
```

### Start a server
Example script:
```bash
./colink-server --address 0.0.0.0 --port 2021 --core-uri http://127.0.0.1:2021
```

### Run `reverse_number`

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
    This will print out 2 `user_jwt` tokens. Copy and paste the token of `user 1` in `examples/Remote_and_Proxy_Flows/proxy-demo.yaml` to the `remote_participant_id` field, and the the first line (jwt token of user 0) of `examples/Remote_and_Proxy_Flows/jwts.txt` to the `jwt` field.
    ```yaml
    ...
    ...
    colink_info:
    cl:
        _target_: colink.CoLink
        jwt: #paste the jwt of user 0 here
        coreaddr: "http://127.0.0.1:2021"
    
    remote_participant_id:  #remote participant user id here
    remote_participant_flow_queue: RemoteFlow:ChatFlowServer:input_queue:1 #queue name here

    ...
    ...
    ```
    Finally, copy and paste the second line (jwt token of user 1) of `examples/Remote_and_Proxy_Flows/jwts.txt` to the `jwt` field of `examples/Remote_and_Proxy_Flows/chatflowserver.yaml`:
    ```yaml
    ...
    description: "A flow that answers questions remotely."
    colink_info:
        cl:
            _target_: colink.CoLink
            jwt: #jwt here
            coreaddr: http://127.0.0.1:2021

        load_incoming_states: False

    ...
        
    ```

3. Start the Persistent Flow:
  ```bash
  conda activate coflows
  python flow-server.py 
  ```

4. In another shell, start the "worker nodes" of the Persistent Flow:
  ```bash
  conda activate coflows
  cd examples/Remote_and_Proxy_Flows/
  python simple-invoke-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
  ```

5. In another shell, start the "worker nodes" of the ProxyFlow:
  ```bash
  conda activate coflows
  cd examples/Remote_and_Proxy_Flows/
  python simple-invoke-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt) --vt-public-addr 127.0.0.1
  ```

6. Finally, run the proxy flow:
  ```bash
  conda activate coflows
  cd examples/Remote_and_Proxy_Flows/
  python proxyflow_run.py 
  ```

