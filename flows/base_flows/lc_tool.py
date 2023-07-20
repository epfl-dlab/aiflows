from typing import Any, Dict, List, Optional

from langchain import WikipediaAPIWrapper
from langchain.agents.agent import ExceptionTool
from langchain.agents.tools import InvalidTool
from langchain.tools import BaseTool, Tool
from langchain.tools.file_management.read import ReadFileTool
from langchain.tools.file_management.write import WriteFileTool

from flows.base_flows import AtomicFlow

class GenericLCTool(AtomicFlow):
    lc_tool: BaseTool

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._instantiate()
        self.lc_tool.verbose = False

    @classmethod
    def _validate_parameters(cls, kwargs):
        super()._validate_parameters(kwargs)

        if "tool_type" not in kwargs["flow_config"]:
            raise KeyError("tool_type not specified in the flow_config.")
        
    def _instantiate(self):
        tool_type = self.flow_config["tool_type"]

        if "file" in tool_type:
            root_dir = self.flow_config["root_dir"]

            if tool_type == "read_file":
                self.lc_tool = ReadFileTool(root_dir=root_dir)
            elif tool_type == "write_file":
                self.lc_tool = WriteFileTool(root_dir=root_dir)
            else:
                raise NotImplementedError(f"Instantiation of tool '{tool_type}' not implemented")

            return

        elif tool_type == "exception":
            self.lc_tool = ExceptionTool()
            return
        elif tool_type == "invalid":
            self.lc_tool = InvalidTool()
            return
        
        elif tool_type == "wikipedia":
            func = WikipediaAPIWrapper().run
        else:
            raise NotImplementedError(f"Instantiation of tool '{tool_type}' not implemented")
        
        self.lc_tool = Tool(
            name=self.flow_config["name"],
            description=self.flow_config["description"],
            func=func,
            return_direct=self.flow_config.get("return_direct", False)
        )

    def run(
        self,
        input_data: Dict[str, Any],
        private_keys: Optional[List[str]] = [],
        keys_to_ignore_for_hash: Optional[List[str]] = []
    ) -> Dict[str, Any]:
        data = {k: input_data[k] for k in self.get_input_keys(input_data)}
        observation = self.lc_tool.run(data)
        return {input_data["output_keys"][0]: observation}


if __name__ == "__main__":
    flow_config = {
        "name": "search",
        "description": "useful for when you need to ask with search",

        "tool_type": "wikipedia",
        "input_keys": ["tool_input"],
        "output_keys": ["raw_response"],

        "verbose": False,
        "clear_flow_namespace_on_run_end": False,
    }

    glct = GenericLCTool.instantiate_from_config(flow_config)

    tm = glct.package_input_message(
        data={"tool_input": "current population of china 2020"},
        src_flow=glct,
    )

    obs = glct(tm)
    print(obs.data)
