import os
import sys

from src.toolkits.function_tool import FunctionTool

# 1) A plain Python function
def web_search(query: str, k: int = 5) -> str:
    """Search the web for a query.

    Args:
        query (str): The search query.
        k (int): How many results to return.

    Returns:
        str: Serialized results.
    """
    return f"results for {query} (top {k})"

# 2) Build tool schema directly from signature + docstring
tool = FunctionTool(web_search)
openai_tool_schema = tool.get_openai_tool_schema()
print(openai_tool_schema)
# => pass this schema to OpenAI/vLLM as `tools=[openai_tool_schema]`

# 3) Optional: enable LLM-based synthesis (inject your OpenAI-like client)
# synthesis = SynthesisConfig(enable_schema_synthesis=True, schema_llm=my_llm)
# tool = FunctionTool(web_search, synthesis=synthesis)
# repaired_or_enhanced_schema = tool.get_openai_tool_schema()

# 4) Execute or synthesize output
print(tool("ReAct paper", 3))          # -> calls the real function
# tool_synth = FunctionTool(web_search, synthesis=SynthesisConfig(enable_output_synthesis=True, output_llm=my_llm))
# print(tool_synth("ReAct paper", 3))  # -> LLM simulates the output