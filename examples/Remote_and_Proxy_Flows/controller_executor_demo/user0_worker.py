from aiflows.utils.colink_protocol_utils import get_simple_invoke_protocol
import sys
# python user1_worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ../jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    pop = get_simple_invoke_protocol(__name__, ephemeral_flow_create=None)
    print("Starting simple-invoke-worker for user", sys.argv[4], "\n")
    pop.run()