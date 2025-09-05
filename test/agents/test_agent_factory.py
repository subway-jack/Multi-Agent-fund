import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src.configs.agents import DeepResearchAgentConfig
from src.agents import AgentFactory

chat_agent = AgentFactory.build_from_config(
    DeepResearchAgentConfig.default()
)

question = "Please search for the meaning of life"
result = chat_agent.step(question)
print(result)