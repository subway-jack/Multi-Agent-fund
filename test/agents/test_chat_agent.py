# test/agents/test_chat_agent.py
import os
import sys
import json
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pydantic import BaseModel, Field

# Ensure imports from project root (so we can import src/*)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# OpenAI response types (for building mocked completions)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function as OaiFunction,
)
from openai.types.completion_usage import CompletionUsage

# Project imports
from src.agents import ChatAgent
from src.configs.models import ChatGPTConfig
from src.memories import MemoryRecord
from src.messages import BaseMessage
from src.models import ModelFactory
from src.toolkits import MathToolkit  # we will use toolkit-provided tools
from src.types import (
    ChatCompletion,
    ModelPlatformType,
    ModelType,
    OpenAIBackendRole,
    RoleType,
)

# -----------------------
# Helpers
# -----------------------
def _mk_completion(text: str) -> ChatCompletion:
    """Build a minimal single-choice assistant completion."""
    return ChatCompletion(
        id="mock_response_id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                logprobs=None,
                message=ChatCompletionMessage(
                    content=text,
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
            )
        ],
        created=123456789,
        model="gpt-4o-2024-05-13",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=5, total_tokens=10),
    )


# ================================================================
# 1) Basic step returns a message (synchronous API)
# ================================================================
def test_step_basic_response_sync():
    system_msg = BaseMessage.make_assistant_message("Assistant", "You are helpful.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict={"temperature": 0},
    )
    agent = ChatAgent(system_message=system_msg, model=model)

    # NOTE: model is accessed via self.model
    agent.model.run = MagicMock(return_value=_mk_completion("Hello from mock!"))

    user_msg = BaseMessage.make_user_message("User", "Hi?")
    resp = agent.step(user_msg)

    assert resp.msgs and resp.msgs[0].content == "Hello from mock!"
    assert resp.terminated is False
    assert "id" in resp.info


# ================================================================
# 2) Memory context starts with system message (when provided)
# ================================================================
def test_memory_context_includes_system_message():
    system_msg = BaseMessage.make_assistant_message("Assistant", "Sys.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    agent = ChatAgent(system_message=system_msg, model=model)
    ctx, _ = agent.memory.get_context()
    assert ctx and ctx[0]["role"] == "system"
    assert "Sys." in ctx[0]["content"]


# ================================================================
# 3) Update memory adds a user message
# ================================================================
def test_update_memory_adds_user_message():
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    agent = ChatAgent(model=model)
    user_msg = BaseMessage.make_user_message("User", "Tell me a joke.")
    agent.update_memory(user_msg, OpenAIBackendRole.USER)
    ctx, _ = agent.memory.get_context()
    # No system message for this agent; first should be the user message
    assert ctx and ctx[0]["role"] == "user"
    assert "Tell me a joke." in ctx[0]["content"]


# ================================================================
# 4) Multiple n-samples; .msg property should raise when >1
#    (parametrized -> counts as 2 tests)
# ================================================================
@pytest.mark.parametrize("n", [2, 3])
def test_multiple_return_messages_and_msg_property_error_sync(n):
    cfg = ChatGPTConfig(temperature=0, n=n).as_dict()
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict=cfg,
    )
    agent = ChatAgent(BaseMessage.make_assistant_message("Assistant", "Sys."), model)

    multi = _mk_completion("Sample 1")
    multi.choices = [
        Choice(
            finish_reason="stop",
            index=i,
            logprobs=None,
            message=ChatCompletionMessage(content=f"Sample {i+1}", role="assistant"),
        )
        for i in range(n)
    ]
    agent.model.run = MagicMock(return_value=multi)

    resp = agent.step(BaseMessage.make_user_message("User", "Hi"))
    assert resp.msgs and len(resp.msgs) == n
    with pytest.raises(RuntimeError, match="only available"):
        _ = resp.msg


# ================================================================
# 5) Streaming config: usage summary is returned
# ================================================================
def test_stream_output_usage_summary_sync():
    system_msg = BaseMessage.make_assistant_message("Assistant", "Stream sys.")
    stream_cfg = ChatGPTConfig(temperature=0, n=2, stream=True).as_dict()
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict=stream_cfg,
    )
    agent = ChatAgent(system_message=system_msg, model=model)

    agent.model.run = MagicMock(return_value=_mk_completion("Hello (stream)."))
    resp = agent.step(BaseMessage.make_user_message("User", "Say hi"))

    usage = resp.info.get("usage", {})
    assert usage.get("completion_tokens", 0) > 0
    assert usage.get("prompt_tokens", 0) > 0
    assert usage.get("total_tokens") == usage["completion_tokens"] + usage["prompt_tokens"]


# ================================================================
# 6) Tool-calling with toolkit-provided sync tools (no FunctionTool(name=...))
# ================================================================
def test_tool_calling_math_with_toolkit_sync():
    system_msg = BaseMessage.make_assistant_message("Assistant", "Sys.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )

    # Use MathToolkit-provided tools so names/signatures match your agent's expectations.
    tools = MathToolkit().get_tools()
    agent = ChatAgent(system_message=system_msg, model=model, tools=tools)

    # 1) model asks to call multiply
    tool_call_completion = ChatCompletion(
        id="mock_tool_call",
        choices=[
            Choice(
                finish_reason="tool_calls",
                index=0,
                logprobs=None,
                message=ChatCompletionMessage(
                    content=None,
                    role="assistant",
                    function_call=None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            id="call_1",
                            function=OaiFunction(
                                name="multiply",  # must match toolkit tool name
                                arguments='{"a": 2, "b": 8, "decimal_places": 0}',
                            ),
                            type="function",
                        )
                    ],
                ),
            )
        ],
        created=1,
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=10, prompt_tokens=10, total_tokens=20),
    )

    # 2) model returns final answer
    final_completion = _mk_completion("The result is 16.")
    agent.model.run = MagicMock(side_effect=[tool_call_completion, final_completion])

    resp = agent.step(BaseMessage.make_user_message("User", "Compute 2*8"))
    tool_calls = resp.info.get("tool_calls", [])

    assert tool_calls and tool_calls[0].tool_name == "multiply"
    assert tool_calls[0].args == {"a": 2, "b": 8, "decimal_places": 0}
    assert tool_calls[0].result == 16
    assert resp.msgs and resp.msgs[0].content == "The result is 16."


# ================================================================
# 7) Message window trimming keeps only last N user turns
# ================================================================
def test_message_window_trimming():
    system_msg = BaseMessage.make_assistant_message("Assistant", "Sys.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    agent = ChatAgent(system_message=system_msg, model=model, message_window_size=2)

    # Push 5 user messages into memory
    for i in range(5):
        agent.memory.write_records(
            [
                MemoryRecord(
                    message=BaseMessage.make_user_message("User", f"Msg {i}"),
                    role_at_backend=OpenAIBackendRole.USER,
                )
            ]
        )

    openai_messages, _ = agent.memory.get_context()
    # Expect only the last 2 (align with your implementation)
    assert len(openai_messages) == 2


# ================================================================
# 8) set_output_language updates system content once
# ================================================================
def test_set_output_language_single():
    system_msg = BaseMessage.make_assistant_message("Assistant", "You are a helper.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    agent = ChatAgent(system_message=system_msg, model=model)
    assert agent.output_language is None

    agent.output_language = "French"

    ctx, _ = agent.memory.get_context()
    assert ctx and ctx[0]["role"] == "system"
    assert "output text in French" in ctx[0]["content"]


# ================================================================
# 9) Structured response with Pydantic response_format
# ================================================================
def test_step_with_response_format_parsing_sync():
    class JokeResponse(BaseModel):
        joke: str = Field(description="a joke")
        funny_level: str = Field(description="Funny level, from 1 to 10")

    system_msg = BaseMessage.make_assistant_message("Assistant", "You help.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict={"temperature": 0},
    )
    agent = ChatAgent(system_message=system_msg, model=model)

    # Mock: backend returns JSON string matching the schema
    completion = _mk_completion(
        json.dumps(
            {"joke": "What do you call fake spaghetti? An impasta!", "funny_level": "6"}
        )
    )
    agent.model.run = MagicMock(return_value=completion)

    user_msg = BaseMessage.make_user_message("User", "Tell a joke.")
    resp = agent.step(user_msg, response_format=JokeResponse)

    parsed = json.loads(resp.msg.content)
    assert set(["joke", "funny_level"]).issubset(parsed.keys())
    assert parsed["joke"].startswith("What do you call fake spaghetti?")


# ================================================================
# 10) Simple vision test (token_limit set high to avoid fallback paths)
# ================================================================
def test_chat_agent_vision_yes_no_sync():
    system_msg = BaseMessage.make_assistant_message("Assistant", "You help.")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict=ChatGPTConfig(temperature=0, max_tokens=50).as_dict(),
    )
    # Large token_limit to avoid hitting any token-exceeded fallback path
    agent = ChatAgent(system_message=system_msg, model=model, token_limit=10**9)

    # Build an in-memory blue PNG
    img = Image.new("RGB", (64, 64), "blue")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    img2 = Image.open(buf)

    user_msg = BaseMessage(
        role_name="User",
        role_type=RoleType.USER,
        meta_dict={},
        content="Is this image blue? Answer yes or no.",
        image_list=[img2],
        image_detail="low",
    )

    # Mock model reply
    agent.model.run = MagicMock(
        return_value=ChatCompletion(
            id="mock_vision_id",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    logprobs=None,
                    message=ChatCompletionMessage(
                        content="Yes.",
                        role="assistant",
                        function_call=None,
                        tool_calls=None,
                    ),
                )
            ],
            created=2,
            model="gpt-4o-2024-05-13",
            object="chat.completion",
            usage=CompletionUsage(completion_tokens=2, prompt_tokens=100, total_tokens=102),
        )
    )

    resp = agent.step(user_msg)
    assert resp.msgs and resp.msgs[0].content.strip().lower().startswith("yes")
