"""
主要的测试配置文件。

导入所有测试fixtures，确保它们可用于所有测试。
"""
import os
# 手动设置测试环境变量，替代pytest.ini中的env配置
os.environ["ENVIRONMENT"] = "test"
os.environ["PYTEST_RUNNING"] = "true"

# 导入所有fixtures，使它们可以在测试中使用
from tests.fixtures import *

# 原始的代码已移动到fixtures目录中的各个模块 