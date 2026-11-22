"""服务依赖工厂（FastAPI 原生 Depends）

约定：
- Resource 统一注入 get_*_service
- Service 内部组合 Repository（不要在 Resource 注入 Repository）
- 本文件由脚手架在生成新表时追加 get_*_service /（可选）get_*_repository
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session

# ---- 脚手架追加区：import Service / Repository，并注册 get_*_service ----
# 示例（以表 sample_item 为例，实际按生成的表名替换）：
# from .sample_item_service import SampleItemService
# from repository.sample_item_repository import SampleItemRepository
#
# def get_sample_item_service(db: AsyncSession = Depends(get_async_session)) -> SampleItemService:
#     return SampleItemService(db)
#
# def get_sample_item_repository(db: AsyncSession = Depends(get_async_session)) -> SampleItemRepository:
#     return SampleItemRepository(db)  # 仅供 Service/测试使用，Resource 勿注入
