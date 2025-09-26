from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path

"""
Ensure project imports work in tests without setting PYTHONPATH.
Adds both the repository root and <root>/src to sys.path.

Pytest auto-discovers conftest.py and executes it before collecting tests,
so this path tweak applies to all tests under this directory and its subfolders.
"""

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent          # adjust to THIS_DIR.parents[2] if needed
SRC_DIR = REPO_ROOT / "src"

for p in (REPO_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


# 测试标记配置
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "slow: 标记测试为慢速测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line("markers", "unit: 标记为单元测试")
    config.addinivalue_line("markers", "binance: 标记为币安API相关测试")
    config.addinivalue_line("markers", "network: 标记为需要网络连接的测试")


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    from src.config.config_manager import config_manager
    return config_manager


@pytest.fixture(scope="session")
def binance_client():
    """币安客户端fixture"""
    from src.core.binance_client import binance_client
    return binance_client


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 在每个测试前执行的设置
    yield
    # 在每个测试后执行的清理

