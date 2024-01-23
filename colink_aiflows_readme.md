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
    This will print out 2 `user_jwt` tokens. Copy and paste the token of `user 1` it in `examples/Remote_and_Proxy_Flows/sequential_proxy.yaml` to the `participant_user_id` field:
    ```yaml
    ...
    ...
    # configuration of subflows
    subflows_config:
    first_reverse_flow:
        _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
        name: "ReverseNumberFirst"
        description: "A flow that takes in a number and reverses it."
        usage_type: "ProxyFlow"
        participant_user_id: #Paste the token of user 1 here
    ...
    ...
    ```
3. Start the "flow initiator":
  ```bash
  conda activate coflows
  python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt) --vt-public-addr 127.0.0.1
  ```

4. In another shell, start the "flow server":
  ```bash
  conda activate coflows
  cd examples/Remote_and_Proxy_Flows/
  python flow_server.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
  ```

5. Finally, in a new shell run `reverse_number/user-launch-flow.py`:
  ```bash
  conda activate coflows
  cd examples/Remote_and_Proxy_Flows/
  python user-launch-flow.py
  ```

