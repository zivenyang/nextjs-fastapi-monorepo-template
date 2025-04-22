"""
测试fixtures包。

通过导入所有fixtures模块，确保pytest能自动发现它们。
pytest加载fixtures时会查找conftest.py文件和所有导入的fixture，包括通过__init__.py导入的模块。
"""

# 导入所有fixture模块，确保pytest能发现它们
from tests.fixtures.database import *  # noqa: F401, F403
from tests.fixtures.http_client import *  # noqa: F401, F403
from tests.fixtures.users import *  # noqa: F401, F403
from tests.fixtures.auth import *  # noqa: F401, F403
from tests.fixtures.redis import * # noqa: F401, F403
