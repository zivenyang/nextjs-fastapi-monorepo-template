#!/usr/bin/env python
"""
应用程序启动脚本，支持不同环境配置
使用方法:
    python run.py                  # 使用默认环境(.env)
    python run.py --env test       # 使用测试环境(.env.test)
    python run.py --env production # 使用生产环境(.env.production)
"""
import argparse
import os
import sys
import uvicorn

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="运行FastAPI应用程序")
    parser.add_argument(
        "--env", "-e", 
        choices=["development", "test", "production"], 
        default="development",
        help="运行环境 (development, test, production)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0", 
        help="监听主机 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="监听端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="启用热重载 (开发模式)"
    )
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置环境变量
    os.environ["ENVIRONMENT"] = args.env
    
    print(f"启动API服务器 (环境: {args.env})")
    
    # 使用uvicorn启动应用程序
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port,
        reload=args.reload,
    )

if __name__ == "__main__":
    main() 