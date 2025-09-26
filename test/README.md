# 测试目录说明

本目录包含项目的所有测试文件，使用 pytest 框架进行测试管理。

## 目录结构

```
test/
├── __init__.py              # 测试包初始化
├── conftest.py             # pytest 配置和共享 fixtures
├── pytest.ini             # pytest 配置文件
├── README.md               # 本文档
├── core/                   # 核心功能测试
│   ├── __init__.py
│   ├── test_binance_client.py      # 币安客户端测试
│   └── test_binance_integration.py # 币安集成测试
├── agents/                 # 智能体测试
├── toolkits/              # 工具包测试
├── sandbox/               # 沙盒测试
└── utils_test/            # 工具函数测试
```

## 测试标记 (Markers)

项目使用以下 pytest 标记来分类和控制测试执行：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.network` - 需要网络连接的测试
- `@pytest.mark.binance` - 币安API相关测试
- `@pytest.mark.slow` - 执行时间较长的测试

## 运行测试

### 运行所有测试
```bash
python -m pytest test/
```

### 运行特定目录的测试
```bash
python -m pytest test/core/
```

### 根据标记运行测试
```bash
# 只运行单元测试
python -m pytest test/ -m "unit"

# 只运行币安相关测试
python -m pytest test/ -m "binance"

# 运行需要网络的币安测试
python -m pytest test/ -m "binance and network"

# 跳过慢速测试
python -m pytest test/ -m "not slow"
```

### 详细输出
```bash
python -m pytest test/ -v -s
```

### 生成测试报告
```bash
python -m pytest test/ --tb=short
```

## 币安API测试

币安API测试位于 `test/core/` 目录下：

- `test_binance_client.py` - 币安客户端基础功能测试
- `test_binance_integration.py` - 币安集成测试

### 测试配置

测试使用以下环境变量和配置：
- `BINANCE_API_KEY` - 币安API密钥
- `BINANCE_API_SECRET` - 币安API密钥
- 配置文件：`src/config/user_config.json`

### 测试结果

当前币安API测试状态：
- ✅ 市场数据获取正常
- ✅ 批量价格获取正常  
- ✅ K线数据获取正常
- ✅ API调用频率限制测试正常
- ⚠️ 连接测试可能因网络延迟失败（不影响核心功能）
- ⏭️ 账户信息测试已跳过（需要特殊权限）

## 添加新测试

1. 在相应目录下创建测试文件（以 `test_` 开头）
2. 导入必要的模块和 fixtures
3. 使用适当的 pytest 标记
4. 编写测试函数（以 `test_` 开头）

示例：
```python
import pytest
from src.core.some_module import SomeClass

@pytest.mark.unit
def test_some_function():
    """测试某个函数"""
    result = SomeClass().some_method()
    assert result is not None
```

## 注意事项

1. 所有测试文件必须以 `test_` 开头
2. 测试函数必须以 `test_` 开头
3. 使用适当的 pytest 标记来分类测试
4. 网络相关测试应该有适当的错误处理
5. 长时间运行的测试应该标记为 `@pytest.mark.slow`