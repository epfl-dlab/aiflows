# IO_keys


## Description

`input_keys` and `output_keys` are interface of the associated Flow.
At runtime, the Flow will check if the input_keys and output_keys are in the input and output of the Flow.
If not, the Flow will raise an error.


## keys w.r.t. `run` or `__call__`

In theory, Flows should have two pairs of keys: one for `run` and one for `__call__`, which we call `run_input_keys, run_output_keys, call_input_keys, call_output_keys` in the following.

Below is the working pipeline of a Flow:
```
__call__():
    - assert call_input_keys(x) we can not assert call_input_keys here, because we allow IDT to change the input keys
    - input_data_transformations
      - assert idt_input_keys
      - assert idt_output_keys
    - run():
        - assert run_input_keys ** input_keys **
        - run_implementation
        - assert run_output_keys
    - output_data_transformations
      - assert odt_input_keys
      - assert odt_output_keys    
    - assert call_output_keys ** output_keys **
```

In our current implementation, we only have one pair of keys, and users(including me) can be easily confused and raise the following questions:
- is the key for `run` or `__call__`?
- supposed I have two flows, `flow1` and `flow2`, and I want to connect them, how should I set the keys?
- When I use `DataTransformation`, how will the keys be affected?

For question 1, our current implementation is that:
- `input_keys` are `run_input_keys`: 
    - cf `https://github.com/epfl-dlab/flows/blob/main/flows/base_flows/abstract.py#L323`. The `input_keys` are checked right before the `run` method is called.
- `output_keys` are `call_output_keys`




The working flow of a Flow is as follows:
```
__call__:
    _preprocess(package_input_message)
        - _apply_input_data_transformations
        - fetch data based on input_keys
    run
    _postprocess:
        - _apply_output_data_transformations
```

```


