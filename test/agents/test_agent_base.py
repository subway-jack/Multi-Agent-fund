import pytest

from src.agents import BaseAgent


class DummyAgent(BaseAgent):
    def __init__(self):
        self.step_count = 0

    def reset(self):
        self.step_count = 0

    def step(self):
        self.step_count += 1


def test_base_agent():
    with pytest.raises(TypeError):
        BaseAgent()


def test_dummy_agent():
    agent = DummyAgent()
    assert agent.step_count == 0
    agent.step()
    assert agent.step_count == 1
    agent.reset()
    assert agent.step_count == 0
    agent.step()
    assert agent.step_count == 1
    agent.step()
    assert agent.step_count == 2
