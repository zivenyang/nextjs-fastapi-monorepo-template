#!/usr/bin/env python
"""
测试运行脚本，提供更直观的测试执行方式
使用方法:
    python run_tests.py                  # 运行所有测试
    python run_tests.py --api            # 只运行API测试
    python run_tests.py --auth           # 只运行认证测试
    python run_tests.py --db             # 只运行数据库测试
    python run_tests.py --unit           # 只运行单元测试
    python run_tests.py -v               # 详细输出
    python run_tests.py --cov            # 带覆盖率报告
    python run_tests.py --setup-db       # 运行测试前设置数据库
"""
import os
import sys
import argparse
import subprocess

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="运行API测试")
    
    # 测试选择参数
    test_group = parser.add_argument_group("测试类型")
    test_group.add_argument("--api", action="store_true", help="只运行API测试")
    test_group.add_argument("--auth", action="store_true", help="只运行认证测试")
    test_group.add_argument("--db", action="store_true", help="只运行数据库测试")
    test_group.add_argument("--unit", action="store_true", help="只运行单元测试")
    test_group.add_argument("--path", type=str, help="运行指定路径的测试")
    
    # 输出参数
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    output_group.add_argument("--cov", action="store_true", help="生成测试覆盖率报告")
    
    # 数据库参数
    db_group = parser.add_argument_group("数据库选项")
    db_group.add_argument("--setup-db", action="store_true", help="在运行测试前设置数据库")
    
    return parser.parse_args()

def setup_test_database():
    """设置测试数据库"""
    print("正在设置测试数据库...")
    
    # 导入并运行setup_test_db模块
    try:
        # 检查setup_test_db.py是否存在
        setup_db_path = os.path.join(os.path.dirname(__file__), "setup_test_db.py")
        if not os.path.exists(setup_db_path):
            print("错误: setup_test_db.py不存在")
            return False
            
        # 运行数据库设置脚本
        result = subprocess.run([sys.executable, setup_db_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"设置测试数据库失败: {result.stderr}")
            return False
            
        print(result.stdout.strip())
        print("测试数据库设置完成")
        return True
        
    except Exception as e:
        print(f"设置测试数据库时出错: {e}")
        return False

def main():
    """主函数"""
    args = parse_args()
    
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "test"
    
    # 设置测试数据库（如果需要）
    if args.setup_db:
        if not setup_test_database():
            print("因为数据库设置失败，测试中止")
            return 1
    
    # 构建pytest命令参数
    pytest_args = ["pytest"]
    
    # 处理测试类型
    if args.api:
        pytest_args.append("-m")
        pytest_args.append("api")
    elif args.auth:
        pytest_args.append("-m")
        pytest_args.append("auth")
    elif args.db:
        pytest_args.append("-m")
        pytest_args.append("db")
    elif args.unit:
        pytest_args.append("-m")
        pytest_args.append("unit")
    
    # 处理路径
    if args.path:
        pytest_args.append(args.path)
    
    # 处理输出选项
    if args.verbose:
        pytest_args.append("-v")
    
    # 处理覆盖率
    if args.cov:
        pytest_args.append("--cov=app")
        pytest_args.append("--cov-report=term")
        pytest_args.append("--cov-report=html")
    
    # 默认设置
    if not args.path and not any([args.api, args.auth, args.db, args.unit]):
        pytest_args.append("tests")
    
    print(f"运行测试: {' '.join(pytest_args)}")
    
    # 执行测试
    result = subprocess.run(pytest_args, capture_output=False)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 