# How to run examples
To run examples from this directory, you need to first:
1. start colink server
2. generate user jwt
3. run coflows-scheduler with your user jwt
4. run at least two dispatch workers with your user jwt (make sure to set the flow_modules_base_path argument to this directory when starting the workers)
e.g.
``python dispatch_worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" path_to_jwts/jwts.txt) --flow_modules_base_path ../../examples/coflows/``
5. make sure the flow_modules directory contains the flow modules referenced in the examples you wish to run
6. run the examples with your user jwt
e.g.
``python run_reverse_number.py  --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" path_to_jwts/jwts.txt)``

Check out what happened to storage at https://colink.run/#
