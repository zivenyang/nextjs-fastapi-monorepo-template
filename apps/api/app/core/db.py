from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import get_logger

# 创建模块日志记录器
logger = get_logger(__name__)

# 数据库引擎配置 - 根据环境设置echo参数
echo = settings.DEBUG
engine = create_async_engine(
    str(settings.DATABASE_URL), 
    echo=echo,      # 调试模式时输出SQL
    echo_pool=echo, # 调试模式时输出连接池信息
    future=True
)

logger.info(f"数据库引擎已创建 (URL: {settings.DATABASE_URL})")


async def init_db():
    """初始化数据库，创建所有表"""
    logger.info("开始初始化数据库...")
    try:
        async with engine.begin() as conn:
            logger.debug("创建数据库表")
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        raise


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    logger.debug("创建新的数据库会话")
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库会话出错: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            logger.debug("关闭数据库会话")