from flows.application_flows.LCToolFlowModule.LCToolFlow import LCToolFlow


if __name__ == "__main__":
    from flows.flow_launchers import FlowLauncher

    curr_flow = LCToolFlow.instantiate_from_default_config()

    input_data = [
        {
            "id": 1,
            "query": "switzerland gdp per capita 2023",
        },
    ]

    _, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)
    print(human_readable_outputs)
