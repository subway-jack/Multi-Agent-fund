# tests/test_sandbox_toolkit.py
# ------------------------------------------------------------
# Minimal smoke test for SandboxToolkit + FunctionTool.
# It prints the OpenAI tool schemas and executes a few calls.
# ------------------------------------------------------------

import os
import sys
from pprint import pprint
from pprint import PrettyPrinter
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src.toolkits.sandbox_toolkit import SandboxToolkit



def main():
    # 1) Create the toolkit.
    #    Override defaults so the test doesn't try to upload missing files or install packages.
    toolkit = SandboxToolkit(
        default_file_map={},          # avoid uploading non-existent files
        default_requirements=[],      # avoid default pip installs
        bootstrap_on_init=False,      # bootstrap lazily at first call
        memory_limit_mb=256,
        timeout_minutes=3,
    )

    # 2) Get the two tools (file_tool, code_tool) as FunctionTool objects
    tools = toolkit.get_tools()
    assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"

    # Map by function name for convenience
    tool_by_name = {t.get_function_name(): t for t in tools}
    file_tool = tool_by_name["file_tool"]
    code_tool = tool_by_name["code_tool"]

    # 3) Print OpenAI tool schemas (these can be passed to LLMs as `tools=[...]`)
    print("\n=== OpenAI Tool Schemas ===")
    PrettyPrinter(width=200, compact=True).pprint(file_tool.get_openai_tool_schema())
    PrettyPrinter(width=200, compact=True).pprint(code_tool.get_openai_tool_schema())

    # 4) Exercise file_tool: save then read
    print("\n=== file_tool: save ===")
    save_res = file_tool(
        "save",
        "tmp/test_sandbox_toolkit.txt",
        "Hello from SandboxToolkit!\nLine 2.",
    )
    pprint(save_res)

    print("\n=== file_tool: read ===")
    read_res = file_tool("read", "tmp/test_sandbox_toolkit.txt")
    pprint(read_res)

    # 5) Exercise code_tool: run Python code that reads the file and prints its content
    print("\n=== code_tool: run_code (Python) ===")
    py_code = r"""
import sys, pathlib
p = pathlib.Path("tmp/test_sandbox_toolkit.txt")
print("File exists:", p.exists())
if p.exists():
    print("Content:")
    print(p.read_text())
"""
    run_code_res = code_tool(
        "run_code",
        code=py_code,
        env_requirements=[],          
    )
    pprint(run_code_res)

    # 6) Exercise code_tool: run a simple bash command
    print("\n=== code_tool: run_bash (echo) ===")
    run_bash_res = code_tool("run_bash", bash_cmd="echo hello_from_bash")
    pprint(run_bash_res)

    # 7) (Optional) Demonstrate FunctionTool with synthesis config (commented)
    # synthesis = SynthesisConfig(enable_schema_synthesis=True, schema_llm=my_llm_client)
    # file_tool_with_synth = FunctionTool(toolkit.file_tool, synthesis=synthesis)
    # repaired_schema = file_tool_with_synth.get_openai_tool_schema()
    # pprint(repaired_schema)

    print("\nAll SandboxToolkit smoke tests completed.")


if __name__ == "__main__":
    main()