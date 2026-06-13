#!/usr/bin/env python3
"""
测试运行脚本

提供便捷的测试执行入口
"""

import argparse
import subprocess
import sys
import os


def run_tests(test_path=None, coverage=False, verbose=False):
    """
    运行测试
    
    Args:
        test_path: 测试路径（可选）
        coverage: 是否生成覆盖率报告
        verbose: 是否详细输出
    """
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd = ["coverage", "run", "-m", "pytest"] + cmd[1:]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if coverage:
            print("\nGenerating coverage report...")
            subprocess.run(["coverage", "report"], check=True)
            subprocess.run(["coverage", "html"], check=True)
            print("Coverage report generated at htmlcov/index.html")
        
        return 0
    except subprocess.CalledProcessError as e:
        print("Test failed with error:", e.stderr)
        return e.returncode


def run_unit_tests():
    """运行单元测试"""
    return run_tests("tests/", verbose=True)


def run_integration_tests():
    """运行集成测试"""
    return run_tests("tests/test_api_integration.py", verbose=True)


def run_enterprise_evaluation_tests():
    """运行企业评价模块测试"""
    return run_tests("tests/test_enterprise_evaluation.py", verbose=True)


def run_candidate_evaluation_tests():
    """运行候选人评价模块测试"""
    return run_tests("tests/test_candidate_evaluation.py", verbose=True)


def run_matching_engine_tests():
    """运行匹配引擎测试"""
    return run_tests("tests/test_matching_engine.py", verbose=True)


def run_all_tests_with_coverage():
    """运行所有测试并生成覆盖率报告"""
    return run_tests("tests/", coverage=True, verbose=True)


def main():
    parser = argparse.ArgumentParser(description="JobAgent测试运行器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 子命令
    subparsers.add_parser("all", help="运行所有测试")
    subparsers.add_parser("unit", help="运行单元测试")
    subparsers.add_parser("integration", help="运行集成测试")
    subparsers.add_parser("enterprise", help="运行企业评价测试")
    subparsers.add_parser("candidate", help="运行候选人评价测试")
    subparsers.add_parser("matching", help="运行匹配引擎测试")
    subparsers.add_parser("coverage", help="运行所有测试并生成覆盖率报告")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置环境变量
    os.environ["PYTHONPATH"] = "src"
    
    # 执行对应命令
    commands = {
        "all": run_unit_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "enterprise": run_enterprise_evaluation_tests,
        "candidate": run_candidate_evaluation_tests,
        "matching": run_matching_engine_tests,
        "coverage": run_all_tests_with_coverage
    }
    
    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())