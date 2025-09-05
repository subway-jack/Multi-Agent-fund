import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from typing import List
from src.agents import ChatAgent
from src.messages import OpenAIMessage
from src.types import ModelPlatformType, ModelType
from src.models import ModelFactory
from typing import Any, ClassVar, Dict, List, Optional
from src.types import CodeReport,PlayReport
from pydantic import BaseModel, Field

import json
import re
from typing import Any, Optional, Type, Union

from pydantic import BaseModel, ValidationError

def extract_payload_from_response(
    response: Any,
    model_cls: Optional[Type[BaseModel]] = None,
    *,
    scope_final: bool = True,
    strip_fence: bool = True,
    auto_json: bool = True,
) -> Union[BaseModel, dict, list, str]:
    """
    Extract payload from your ChatAgentResponse-like object.

    Assumes:
      - `response.msgs` is a list of BaseMessage
      - last message has `.content` (str/dict/list) and optional `.parsed` (Pydantic)

    If `model_cls` is provided:
      1) If last_msg.parsed is an instance of `model_cls`, return it.
      2) Else try to revalidate last_msg.parsed (if it has model_dump or is dict/list).
      3) Else parse JSON from last_msg.content and validate.

    If `model_cls` is None:
      - Return processed `content`:
        * optionally scope to the last <final>...</final>
        * optionally strip ``` / ```json fences
        * optionally try json.loads; if it succeeds, return dict/list; else return string
    """

    # 1) last message
    msgs = getattr(response, "msgs", None)
    if not msgs:
        raise ValueError("response.msgs is empty or missing")
    last_msg = msgs[-1]

    # 2) structured path: prefer parsed if model_cls is provided
    if model_cls is not None:
        parsed = getattr(last_msg, "parsed", None)
        if isinstance(parsed, model_cls):
            return parsed
        if parsed is not None:
            if hasattr(parsed, "model_dump"):
                try:
                    return model_cls.model_validate(parsed.model_dump())
                except ValidationError:
                    pass
            if isinstance(parsed, (dict, list)):
                return model_cls.model_validate(parsed)

    # 3) fallback to content
    content = getattr(last_msg, "content", "")

    # If no schema requested: return processed content (not the parsed object)
    if model_cls is None:
        if isinstance(content, (dict, list)):
            return content  # already structured

        text = str(content).strip()

        if scope_final:
            finals = list(re.finditer(r"<final>(.*?)</final>", text, flags=re.S | re.I))
            if finals:
                text = finals[-1].group(1).strip()

        if strip_fence and "```" in text:
            blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.I)
            if blocks:
                text = blocks[-1].strip()

        if auto_json:
            try:
                return json.loads(text)
            except Exception:
                pass  # not valid JSON; return cleaned string

        return text

    # Schema requested: validate dict/list or parse from string JSON
    if isinstance(content, (dict, list)):
        return model_cls.model_validate(content)

    if not isinstance(content, str):
        raise TypeError(f"Unsupported content type for parsing: {type(content)}")

    text = content.strip()
    if scope_final:
        finals = list(re.finditer(r"<final>(.*?)</final>", text, flags=re.S | re.I))
        if finals:
            text = finals[-1].group(1).strip()
    if strip_fence and "```" in text:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.I)
        if blocks:
            text = blocks[-1].strip()

    payload = json.loads(text)
    return model_cls.model_validate(payload)

class ReasoningStep(BaseModel):
    step: str = Field(
        ..., description="A single step in the reasoning process."
    )
# 1) 构建模型
single_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4_1_MINI,
    model_config_dict={"temperature": 0},
)

# 2) 准备消息（OpenAI 风格）
user_prompt = '''
"""
Inverted Pendulum Swingup Environment

Purpose:
This module implements a classic inverted pendulum swingup environment for control and reinforcement learning.

API:
- __init__(self, seed: int | None = None): Initialize environment with optional random seed.
- set_state(self, state): Set environment state from observation (cos(theta), sin(theta), angular velocity).
- step(self, action) -> (observation, reward, done): Apply torque action, advance simulation by dt, return next observation, reward, and done flag.

State:
- theta: pendulum angle in radians, normalized to [-pi, pi], 0 is upright.
- theta_dot: angular velocity in radians/sec, clamped to [-8, 8].

Action:
- torque: ndarray shape (1,), float in [-2.0, 2.0].

Observation:
- ndarray shape (3,): [cos(theta), sin(theta), theta_dot], with ranges:
  cos(theta) in [-1,1], sin(theta) in [-1,1], theta_dot in [-8,8].

Determinism/Seed:
- Random seed controls initial state sampling.
- Dynamics deterministic given fixed seed and action sequence.

Assumptions:
- Pendulum length and mass fixed (length=1m, mass=1kg).
- Torque applied at free end.
- Time step dt=0.02s.
- Dynamics integrated with Explicit Euler method.

"""

import numpy as np

class Environment:
    def __init__(self, seed: int | None = None):
        import math
        self._pi = math.pi
        self._dt = 0.02  # time step in seconds
        self._max_torque = 2.0
        self._max_speed = 8.0
        self._min_speed = -8.0
        self._min_torque = -2.0
        self._max_steps = 2000  # max episode length

        # Physical constants
        self._g = 9.8  # gravity m/s^2
        self._m = 1.0  # mass kg
        self._l = 1.0  # length m

        # State variables
        # theta: angle in radians, normalized to [-pi, pi], 0 is upright
        # theta_dot: angular velocity in rad/s
        self.theta = 0.0
        self.theta_dot = 0.0

        # Step counter
        self._step_count = 0

        # Random number generator
        self._rng = np.random.default_rng(seed)

        # Initialize state randomly
        self._reset_random_state()

    def _reset_random_state(self):
        # Random angle in [-pi, pi]
        self.theta = self._rng.uniform(-self._pi, self._pi)
        # Random angular velocity in [-1, 1]
        self.theta_dot = self._rng.uniform(-1.0, 1.0)
        self._step_count = 0

    def seed(self, seed: int):
        """Set the random seed for reproducibility."""
        self._rng = np.random.default_rng(seed)

    def _normalize_angle(self, angle):
        # Normalize angle to [-pi, pi]
        from math import pi
        a = angle
        while a > pi:
            a -= 2 * pi
        while a < -pi:
            a += 2 * pi
        return a

    def set_state(self, state):
        """
        Set the environment state from an observation.
        state: array-like with shape (3,) representing [cos(theta), sin(theta), theta_dot]
        """
        import numbers
        # Validate input type and shape
        if not (isinstance(state, (list, tuple, np.ndarray))):
            raise TypeError(f"State must be list, tuple, or ndarray, got {type(state)}")

        arr = np.asarray(state, dtype=np.float64)
        if arr.shape != (3,):
            raise ValueError(f"State must have shape (3,), got {arr.shape}")

        cos_theta, sin_theta, theta_dot = arr

        # Validate ranges
        if not (-1.0 <= cos_theta <= 1.0):
            raise ValueError(f"cos(theta) must be in [-1,1], got {cos_theta}")
        if not (-1.0 <= sin_theta <= 1.0):
            raise ValueError(f"sin(theta) must be in [-1,1], got {sin_theta}")
        if not (self._min_speed <= theta_dot <= self._max_speed):
            raise ValueError(f"Angular velocity must be in [{self._min_speed},{self._max_speed}], got {theta_dot}")

        # Reconstruct theta from cos and sin
        theta = np.arctan2(sin_theta, cos_theta)

        # Normalize angle
        theta = self._normalize_angle(theta)

        self.theta = theta
        self.theta_dot = theta_dot
        self._step_count = 0  # reset step count

    def step(self, action):
        """
        Apply action (torque) and advance simulation by one time step.

        Parameters:
        - action: ndarray or scalar representing torque, shape (1,) or scalar, in [-2.0, 2.0]

        Returns:
        - observation: ndarray shape (3,) [cos(theta), sin(theta), theta_dot]
        - reward: float
        - done: bool (episode termination flag)
        """
        import numbers

        # Validate and canonicalize action
        if isinstance(action, (list, tuple, np.ndarray)):
            arr = np.asarray(action, dtype=np.float64)
            if arr.shape == ():
                # scalar 0-d array
                torque = float(arr)
            elif arr.shape == (1,):
                torque = float(arr[0])
            else:
                raise ValueError(f"Action must be scalar or shape (1,), got shape {arr.shape}")
        elif isinstance(action, numbers.Number):
            torque = float(action)
        else:
            raise TypeError(f"Action must be a number or ndarray/list/tuple, got {type(action)}")

        # Clamp torque to valid range
        if torque < self._min_torque or torque > self._max_torque:
            raise ValueError(f"Torque must be in [{self._min_torque}, {self._max_torque}], got {torque}")

        # Dynamics integration using Explicit Euler
        # Corrected equation:
        # theta_ddot = -(g / l) * sin(theta) + torque / (m * l^2)
        # Since m=1, l=1, simplifies to:
        # theta_ddot = -g * sin(theta) + torque

        theta_ddot = -self._g * np.sin(self.theta) + torque

        # Update state
        self.theta_dot += theta_ddot * self._dt

        # Clamp angular velocity
        self.theta_dot = np.clip(self.theta_dot, self._min_speed, self._max_speed)

        self.theta += self.theta_dot * self._dt
        self.theta = self._normalize_angle(self.theta)

        # Compute observation
        obs = np.array([np.cos(self.theta), np.sin(self.theta), self.theta_dot], dtype=np.float64)

        # Compute reward
        # r = -(theta^2 + 0.1*theta_dot^2 + 0.001*torque^2)
        # theta normalized to [-pi, pi], 0 is upright
        reward = -(self.theta ** 2 + 0.1 * self.theta_dot ** 2 + 0.001 * torque ** 2)

        # Episode done flag
        done = False
        self._step_count += 1
        if self._step_count >= self._max_steps:
            done = True

        return obs, reward, done


if __name__ == '__main__':
    # Minimal demo
    env = Environment(seed=42)
    print("Initial state:", [np.cos(env.theta), np.sin(env.theta), env.theta_dot])
    for i in range(5):
        action = np.array([0.5])
        obs, reward, done = env.step(action)
        print(f"Step {i+1}: obs={obs}, reward={reward:.4f}, done={done}")
        if done:
            break

请你仔细分析一下这个代码 查看一下哪里有实现不妥当的地方  主要是要符合真实物理 以及真实反馈 中文回答即可
'''
chat_agent = ChatAgent(
    system_message="You are a helpful agent",
    model=single_model,
    auto_save=True,
)

# 3) 同步调用
response = chat_agent.step(user_prompt)

print(response)
code_report = extract_payload_from_response(response)
print(code_report)

# code_report:PlayReport = extract_payload_from_response(response,PlayReport)
# print(code_report)