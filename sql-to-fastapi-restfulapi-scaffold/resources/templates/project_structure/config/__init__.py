"""配置模块 - 多环境配置（单轨）

约定：
- 唯一配置源：`config_unified.py`（BaseConfig + 各环境类）
- 入口：`config_factory.py` 按 FASTAPI_ENV 选环境，并导出兼容别名 `settings`
- 使用方式：`from config import settings`（扁平字段，如 settings.database_url）
- CLI：`python config/manage.py validate|export|compare|template|list-environments`

请勿再增加第二套嵌套 `settings.py`；业务侧统一走本包导出的 `settings`。
"""

from .config_unified import (
    BaseConfig,
    DevelopmentConfig,
    TestingConfig,
    StagingConfig,
    ProductionConfig,
    DockerConfig,
    Environment,
    LogLevel,
)

from .config_factory import (
    get_config,
    get_config_manager,
    reload_config,
    config,
    config_manager,
    settings,
    ConfigFactory,
    ConfigManager,
)

__all__ = [
    "config",
    "config_manager",
    "settings",
    "get_config",
    "get_config_manager",
    "reload_config",
    "ConfigFactory",
    "ConfigManager",
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "StagingConfig",
    "ProductionConfig",
    "DockerConfig",
    "Environment",
    "LogLevel",
]
