#!/usr/bin/env python3
"""
AI Trial Game - 环境检查与启动脚本
"""

import os
import sys
import json
from pathlib import Path

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")

def check_python_deps():
    """检查Python依赖"""
    print("\n[1/5] 检查Python依赖...")

    required = ["fastapi", "uvicorn", "openai", "web3", "dotenv", "pydantic"]
    missing = []

    for pkg in required:
        try:
            if pkg == "dotenv":
                __import__("dotenv")
            else:
                __import__(pkg)
            ok(pkg)
        except ImportError:
            fail(f"{pkg} 未安装")
            missing.append(pkg)

    if missing:
        return False, f"缺少依赖: {', '.join(missing)}\n   运行: pip install {' '.join(missing)}"
    return True, None

def check_env_file():
    """检查.env配置"""
    print("\n[2/5] 检查环境配置...")

    env_path = Path(__file__).parent / "backend" / ".env"
    if not env_path.exists():
        fail(".env 文件不存在")
        return False, f".env 文件不存在\n   复制 backend/.env.example 为 backend/.env 并填写配置"

    ok(".env 文件存在")

    # 读取.env
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

    # 检查必要配置
    issues = []

    api_key = env_vars.get("OPENAI_COMPATIBLE_API_KEY", "")
    if not api_key or api_key.startswith("sk-xxx"):
        warn("OPENAI_COMPATIBLE_API_KEY 未配置 (陪审员对话不可用)")
        issues.append("LLM API Key")
    else:
        ok("OPENAI_COMPATIBLE_API_KEY 已配置")

    base_url = env_vars.get("OPENAI_COMPATIBLE_BASE_URL", "")
    if not base_url:
        warn("OPENAI_COMPATIBLE_BASE_URL 未配置")
    else:
        ok(f"API Base URL: {base_url[:40]}...")

    return True, issues if issues else None

def check_llm_api():
    """检查LLM API连接"""
    print("\n[3/5] 检查LLM API连接...")

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / "backend" / ".env")

        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-3.5-turbo")

        if not api_key or api_key.startswith("sk-xxx"):
            warn("API Key 未配置，跳过连接测试")
            return True, "LLM API 未配置 (说服阶段不可用)"

        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

        # 简单测试
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        ok(f"LLM API 连接成功 (模型: {model})")
        return True, None

    except Exception as e:
        warn(f"LLM API 连接失败: {str(e)[:50]}")
        return True, "LLM API 不可用 (说服阶段无法对话)"

def check_anvil():
    """检查Anvil本地链"""
    print("\n[4/5] 检查Anvil区块链...")

    try:
        from web3 import Web3
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / "backend" / ".env")

        rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if w3.is_connected():
            block = w3.eth.block_number
            ok(f"Anvil 运行中 (区块高度: {block})")
            return True, None
        else:
            warn("Anvil 未运行 (投票功能不可用)")
            return True, "Anvil 未运行 (审判阶段不可用)"

    except Exception as e:
        warn(f"Anvil 检查失败: {str(e)[:40]}")
        return True, "Anvil 未运行 (审判阶段不可用)"

def check_contract():
    """检查合约部署"""
    print("\n[5/5] 检查智能合约...")

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / "backend" / ".env")

        contract_addr = os.getenv("JURY_VOTING_CONTRACT_ADDRESS", "")
        if not contract_addr:
            warn("合约地址未配置 (投票功能不可用)")
            return True, "合约未部署"

        from web3 import Web3
        rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            warn("无法验证合约 (Anvil未运行)")
            return True, "无法验证合约"

        code = w3.eth.get_code(contract_addr)
        if code and len(code) > 2:
            ok(f"合约已部署: {contract_addr[:20]}...")
            return True, None
        else:
            warn("合约地址无代码 (需要重新部署)")
            return True, "合约未部署"

    except Exception as e:
        warn(f"合约检查失败: {str(e)[:40]}")
        return True, "合约检查失败"

def check_content():
    """检查游戏内容"""
    print("\n[附加] 检查游戏内容...")

    content_root = Path(__file__).parent / "content"

    # 卷宗
    dossier = content_root / "case" / "dossier.json"
    if dossier.exists():
        ok("卷宗文件存在")
    else:
        fail("卷宗文件缺失")

    # 证据
    evidence_dir = content_root / "case" / "evidence"
    evidence_files = list(evidence_dir.glob("*.json")) if evidence_dir.exists() else []
    evidence_files = [f for f in evidence_files if not f.name.startswith("_")]
    if evidence_files:
        ok(f"证据文件: {len(evidence_files)} 个")
    else:
        warn("无证据文件")

    # 当事人
    witness_dir = content_root / "witnesses"
    witness_files = list(witness_dir.glob("*.json")) if witness_dir.exists() else []
    witness_files = [f for f in witness_files if not f.name.startswith("_")]
    if witness_files:
        ok(f"当事人文件: {len(witness_files)} 个")
    else:
        warn("无当事人文件")

    # 陪审员
    juror_dir = content_root / "jurors"
    juror_files = list(juror_dir.glob("*.json")) if juror_dir.exists() else []
    juror_files = [f for f in juror_files if not f.name.startswith("_") and not f.name.startswith("test")]
    if juror_files:
        ok(f"陪审员文件: {len(juror_files)} 个")
    else:
        warn("无陪审员文件")

def main():
    print("=" * 50)
    print("  AI Trial Game - 环境检查")
    print("=" * 50)

    errors = []
    warnings = []

    # 依赖检查
    success, msg = check_python_deps()
    if not success:
        errors.append(msg)

    # 环境配置
    success, msg = check_env_file()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.extend(msg)

    # 如果基础依赖有问题，停止
    if errors:
        print("\n" + "=" * 50)
        print(f"{RED}✗ 环境检查失败{RESET}")
        print("=" * 50)
        for e in errors:
            print(f"\n{RED}错误:{RESET} {e}")
        sys.exit(1)

    # LLM API
    success, msg = check_llm_api()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.append(msg)

    # Anvil
    success, msg = check_anvil()
    if msg:
        warnings.append(msg)

    # 合约
    success, msg = check_contract()
    if msg:
        warnings.append(msg)

    # 内容检查
    check_content()

    # 结果汇总
    print("\n" + "=" * 50)

    if errors:
        print(f"{RED}✗ 环境检查失败{RESET}")
        print("=" * 50)
        for e in errors:
            print(f"\n{RED}错误:{RESET} {e}")
        sys.exit(1)

    if warnings:
        print(f"{YELLOW}! 环境检查通过 (有警告){RESET}")
        print("=" * 50)
        print(f"\n{YELLOW}警告:{RESET}")
        for w in warnings:
            print(f"  - {w}")
        print(f"\n{YELLOW}部分功能可能不可用，但游戏可以启动。{RESET}")
    else:
        print(f"{GREEN}✓ 环境检查通过{RESET}")
        print("=" * 50)

    # 询问是否启动
    print("\n是否启动游戏服务器? [Y/n] ", end="")
    try:
        answer = input().strip().lower()
        if answer in ("", "y", "yes"):
            print("\n启动服务器...\n")
            os.chdir(Path(__file__).parent / "backend")
            os.execvp("python3", ["python3", "main.py"])
        else:
            print("已取消")
    except (KeyboardInterrupt, EOFError):
        print("\n已取消")

if __name__ == "__main__":
    main()
