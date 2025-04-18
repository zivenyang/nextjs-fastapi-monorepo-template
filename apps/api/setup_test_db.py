#!/usr/bin/env python
"""
测试数据库设置脚本

这个脚本用于创建和初始化测试数据库 'test_mydb'。
它会创建数据库（如果不存在）并设置所需的权限。

运行方式: python setup_test_db.py
"""
import os
import sys
import asyncio
import asyncpg
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine

# PostgreSQL 连接参数
PG_USER = "postgres"
PG_PASSWORD = "password"  # 根据实际情况修改
PG_HOST = "localhost"
PG_PORT = "5432"
TEST_DB_NAME = "test-mydb"

# 默认数据库（用于创建测试数据库）
DEFAULT_DB_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres"

# 测试数据库URL
TEST_DB_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{TEST_DB_NAME}"

async def setup_test_db():
    """创建和设置测试数据库"""
    print(f"正在设置测试数据库: {TEST_DB_NAME}")
    
    # 连接到默认数据库
    try:
        conn = await asyncpg.connect(DEFAULT_DB_URL)
    except Exception as e:
        print(f"连接到PostgreSQL失败: {e}")
        return False
    
    try:
        # 检查测试数据库是否存在
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        
        # 如果数据库不存在，创建它
        if not db_exists:
            print(f"创建数据库 '{TEST_DB_NAME}'...")
            await conn.execute(f"CREATE DATABASE {TEST_DB_NAME}")
            print(f"数据库 '{TEST_DB_NAME}' 已创建")
        else:
            print(f"数据库 '{TEST_DB_NAME}' 已存在")
        
        # 关闭连接
        await conn.close()
        
        # 连接到测试数据库并创建表结构
        print("初始化测试数据库架构...")
        engine = create_async_engine(TEST_DB_URL)
        
        # 导入所有模型以确保它们被注册
        from app.models.user import User
        
        # 创建表
        async with engine.begin() as conn:
            # 首先删除所有表以确保干净的状态
            await conn.run_sync(SQLModel.metadata.drop_all)
            # 然后创建所有表
            await conn.run_sync(SQLModel.metadata.create_all)
        
        await engine.dispose()
        
        print("测试数据库设置完成!")
        return True
        
    except Exception as e:
        print(f"设置测试数据库时出错: {e}")
        if conn:
            await conn.close()
        return False

if __name__ == "__main__":
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "test"
    
    # 运行设置函数
    success = asyncio.run(setup_test_db())
    
    # 返回适当的退出代码
    sys.exit(0 if success else 1) 