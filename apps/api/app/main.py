from fastapi import FastAPI
import uvicorn
from app.core.db import init_db
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    await init_db()
    yield
    # 关闭时执行
    # 这里可以添加清理代码

app = FastAPI(
    title=settings.PROJECT_NAME, 
    description="一个基于FastAPI的Web API模板",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Hello World", "docs_url": "/docs"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
