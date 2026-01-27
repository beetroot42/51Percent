#!/usr/bin/env python3
"""
AI Trial Game - environment setup and launcher.
Steps: venv -> dependencies -> anvil -> contract deploy -> server start.
"""

import os
import sys
import json
import re
import signal
import subprocess
import time
import shutil
import urllib.request
import urllib.error
from pathlib import Path

# Windows encoding guard: keep UTF-8 output stable
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Color output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Global process tracking
anvil_process = None
anvil_log_file = None
backend_process = None
MODE = None

def ok(msg):
    print(f"  {GREEN}[OK]{RESET} {msg}")

def fail(msg):
    print(f"  {RED}[FAIL]{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")

def info(msg):
    print(f"  {BLUE}[INFO]{RESET} {msg}")

def cleanup_on_exit(signum=None, frame=None):
    """Clean up child processes."""
    global anvil_process, backend_process, anvil_log_file
    print("\n[start.py] Shutting down...")

    if backend_process:
        print("[start.py] Terminating backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

    if anvil_process:
        print("[start.py] Terminating Anvil...")
        anvil_process.terminate()
        try:
            anvil_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            anvil_process.kill()

    if anvil_log_file:
        try:
            anvil_log_file.close()
        except Exception:
            pass

    print("[start.py] Cleanup complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup_on_exit)
signal.signal(signal.SIGTERM, cleanup_on_exit)

def check_venv():
    """Check virtual environment (optional)."""
    print("\n[1/8] Checking virtual environment...")

    venv_path = Path(__file__).parent / "venv"

    # Check if running inside venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if in_venv:
        ok("Virtual environment active")
        return True, None

    if venv_path.exists() and (venv_path / "bin" / "activate").exists():
        warn("Virtual environment exists but is not activated (recommended)")
        info("Activate: source venv/bin/activate  (Linux/Mac)")
        info("         venv\\Scripts\\activate  (Windows)")
        warn("Continuing with system Python...")
    return True, "Virtual environment not active"

def get_python_executable():
    """Get preferred Python executable (venv-first)."""
    project_root = Path(__file__).parent
    candidates = []
    if os.name == "nt":
        candidates.append(project_root / "venv" / "Scripts" / "python.exe")
        candidates.append(project_root / "venv" / "Scripts" / "python")
    else:
        candidates.append(project_root / "venv" / "bin" / "python")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return sys.executable

    # Try to create virtual environment
    warn("Virtual environment not found, creating...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode == 0:
            ok(f"Virtual environment created: {venv_path}")
            warn("Activate the venv and re-run:")
            info("  source venv/bin/activate && python start.py")
            warn("Continuing with system Python...")
            return True, "Virtual environment created but not active"
        else:
            warn("Failed to create venv (python3-venv may be missing)")
            info("Ubuntu/Debian: sudo apt install python3-venv")
            warn("Continuing with system Python...")
            return True, "Virtual environment not active"
    except Exception as e:
        warn(f"Failed to create venv: {str(e)[:50]}")
        warn("Continuing with system Python...")
        return True, "Virtual environment not active"

def check_python_deps():
    """Check and install Python dependencies."""
    print("\n[2/8] Checking Python dependencies...")
    python_exec = get_python_executable()

    # Check pip availability first
    try:
        result = subprocess.run(
            [python_exec, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode != 0:
            fail("pip is not available")
            return False, (
                "Python pip is not installed.\n\n"
                "Fix options:\n"
                "1. Install pip: python3 -m ensurepip --default-pip\n"
                "2. Ubuntu/Debian: sudo apt install python3-pip\n"
                "3. Use venv: sudo apt install python3-venv && python3 -m venv venv && source venv/bin/activate"
            )
        ok(f"pip available: {result.stdout.strip()[:40]}")
    except Exception as e:
        fail("pip check failed")
        return False, f"Unable to check pip: {e}\n   Please ensure pip is installed"

    required = ["fastapi", "uvicorn", "openai", "web3", "python-dotenv", "pydantic"]
    missing = []

    for pkg in required:
        try:
            import_name = "dotenv" if pkg == "python-dotenv" else pkg
            __import__(import_name)
            ok(pkg)
        except ImportError:
            fail(f"{pkg} not installed")
            missing.append(pkg)

    if missing:
        print(f"\n  {YELLOW}Installing missing dependencies...{RESET}")
        requirements_file = Path(__file__).parent / "backend" / "requirements.txt"

        if not requirements_file.exists():
            return False, f"requirements.txt not found: {requirements_file}"

        try:
            result = subprocess.run(
                [python_exec, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            if result.returncode == 0:
                ok("Dependencies installed")
                return True, None
            else:
                # Try --user install
                warn("Trying --user install...")
                result = subprocess.run(
                    [python_exec, "-m", "pip", "install", "--user", "-q", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300
                )
                if result.returncode == 0:
                    ok("Dependencies installed (--user)")
                    return True, None
                else:
                    return False, (
                        f"Dependency install failed:\n{result.stderr[:200]}\n\n"
                        "Please run:\n"
                        "pip install --user -r backend/requirements.txt"
                    )
        except subprocess.TimeoutExpired:
            return False, "Dependency install timed out (>5 minutes)"
        except Exception as e:
            return False, f"Dependency install failed: {e}"

    return True, None

def check_env_file():
    """Check .env configuration."""
    print("\n[3/8] Checking environment config...")

    env_path = Path(__file__).parent / "backend" / ".env"
    if not env_path.exists():
        fail(".env file not found")
        return False, ".env not found\n   Copy backend/.env.example to backend/.env and fill values"

    ok(".env file exists")

    # Read .env
    env_vars = {}
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

    # Check required config
    issues = []

    api_key = env_vars.get("OPENAI_COMPATIBLE_API_KEY", "")
    if not api_key or api_key.startswith("sk-xxx"):
        warn("OPENAI_COMPATIBLE_API_KEY not set (juror chat disabled)")
        issues.append("LLM API Key")
    else:
        ok("OPENAI_COMPATIBLE_API_KEY set")

    base_url = env_vars.get("OPENAI_COMPATIBLE_BASE_URL", "")
    server_port = env_vars.get("SERVER_PORT", "5000")

    if not base_url:
        warn("OPENAI_COMPATIBLE_BASE_URL not set")
    else:
        # Check for loop (base URL pointing to game server)
        if f":{server_port}" in base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
            fail(f"Config error: base URL must not point to game server (port {server_port})")
            return False, (
                "OPENAI_COMPATIBLE_BASE_URL invalid\n"
                f"   Current: {base_url}\n"
                f"   Game server port: {server_port}\n"
                "   This creates a loop.\n\n"
                "   Set a real LLM API base URL, for example:\n"
                "   - https://api.openai.com/v1\n"
                "   - https://api.example.com/v1\n"
                "   - another OpenAI-compatible provider"
            )
        ok(f"API Base URL: {base_url[:50]}...")

    return True, issues if issues else None

def check_llm_api():
    """Check LLM API connectivity."""
    print("\n[4/8] Checking LLM API connection...")

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / "backend" / ".env")

        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "gemini-3-pro-high")

        if not api_key or api_key.startswith("sk-xxx"):
            warn("API key not set, skipping test")
            return True, "LLM API not configured (persuasion disabled)"

        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

        # Test API
        info("Testing API connection...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply 'OK'"}],
            max_tokens=10,
            timeout=10
        )

        reply = response.choices[0].message.content.strip() if response.choices else ""
        if not reply:
            msg = response.choices[0].message if response.choices else None
            reply = getattr(msg, 'reasoning_content', '').strip() if msg else ""

        if not reply:
            fail("LLM API returned empty response")
            return True, "LLM API returned empty response (persuasion may fail)"

        ok("LLM API connection OK")
        ok(f"Model reply: {reply[:40]}")
        return True, None

    except Exception as e:
        error_msg = str(e)
        warn(f"LLM API connection failed: {error_msg[:60]}...")

        # Common error hints
        if "Connection refused" in error_msg or "Couldn't connect" in error_msg:
            fail(f"API service not running ({base_url})")
            info("Fix:")
            port_hint = base_url.split(":")[-1].split("/")[0] if ":" in base_url else "unknown"
            info(f"1. Start your API proxy (port {port_hint})")
            info("2. Or skip API check (persuasion disabled)")
        elif "1033" in error_msg or "530" in error_msg:
            fail("Cloudflare tunnel unreachable")
            info("Check tunnel status or update OPENAI_COMPATIBLE_BASE_URL")
        elif "timeout" in error_msg.lower():
            fail("Connection timeout")
        elif "401" in error_msg or "403" in error_msg:
            fail("Invalid API key or insufficient permissions")

        return True, "LLM API unavailable (persuasion disabled)"

def check_spoon_core():
    """Check spoon-core local dependency and import."""
    print("\n[3/8] Checking spoon-core...")
    project_root = Path(__file__).parent
    spoon_path = (project_root / ".." / "spoon-core-main" / "spoon-core-main").resolve()

    use_spoon_agent = os.getenv("USE_SPOON_AGENT", "true").lower() not in ("false", "0", "no")
    if not spoon_path.exists():
        msg = f"spoon-core path not found: {spoon_path}"
        if use_spoon_agent:
            fail(msg)
            return False, msg
        warn(msg)
        return True, msg

    python_exec = get_python_executable()
    try:
        result = subprocess.run(
            [python_exec, "-c", "import spoon_ai; print(spoon_ai.__name__)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )
    except Exception as e:
        msg = f"spoon-core import check failed: {e}"
        fail(msg)
        return False, msg

    if result.returncode != 0:
        msg = f"spoon-core not importable: {result.stderr.strip()[:120]}"
        if use_spoon_agent:
            fail(msg)
            return False, msg
        warn(msg)
        return True, msg

    ok("spoon-core available")
    return True, None

def check_server_port():
    """Check if server port is available."""
    print("\n[5/9] Checking server port...")

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "backend" / ".env")

    server_host = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port = int(os.getenv("SERVER_PORT", "5000"))

    # Check if port is in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((server_host, server_port))
        sock.close()
        ok(f"Port {server_port} available (host: {server_host})")
        return True, None
    except OSError as e:
        sock.close()
        if e.errno == 98 or e.errno == 10048:  # Address already in use
            fail(f"Port {server_port} is in use")

            # Try to find process
            warn("Looking for process using the port...")
            try:
                # Linux/Mac
                result = subprocess.run(
                    ["lsof", "-ti", f":{server_port}"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    warn(f"Port {server_port} is in use")
                    info(f"PID(s): {', '.join(pids)}")
                    info("Fix:")
                    info(f"  kill -9 {' '.join(pids)}")
                    info("  or change SERVER_PORT")
                    return True, f"Port {server_port} in use (will auto-switch)"
                else:
                    warn(f"Port {server_port} is in use")
                    info("Fix:")
                    info("1. Manually stop the process")
                    info("2. Or let main.py auto-switch")
                    return True, f"Port {server_port} in use (will auto-switch)"
            except FileNotFoundError:
                warn(f"Port {server_port} is in use")
                info("Windows process lookup:")
                info(f"  netstat -ano | findstr :{server_port}")
                info("  taskkill /PID <PID> /F")
                return True, f"Port {server_port} in use (will auto-switch)"
            except Exception as find_err:
                warn(f"Failed to find process: {str(find_err)[:40]}")
                return True, f"Port {server_port} in use (will auto-switch)"
        elif e.errno == 10013:  # Windows permission denied
            fail("Port check failed: permission denied (WinError 10013)")
            warn(f"Binding {server_host} may require admin on Windows")
            info("Fix:")
            info("1. Set SERVER_HOST=127.0.0.1 in backend/.env (recommended)")
            info("2. Or run PowerShell/CMD as Administrator")
            return False, "Port check failed: permission denied\n   Set SERVER_HOST=127.0.0.1"
        else:
            fail(f"Port check failed: {e}")
            return False, f"Port check failed: {e}"


def configure_local_accounts():
    """Auto-configure Anvil default accounts for local mode."""
    local_accounts = {
        "PRIVATE_KEY": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "JUROR_1": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "JUROR_2": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "JUROR_3": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "JUROR_4": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
        "JUROR_5": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
        "JURY_VOTING_PRIVATE_KEYS": ",".join([
            "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
            "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
            "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
            "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
            "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
        ]),
        "RPC_URL": "http://127.0.0.1:8545"
    }

    for key, value in local_accounts.items():
        os.environ[key] = value

    print("✅ Auto-configured Anvil default accounts")


def check_foundry():
    """Check Foundry availability."""
    print("\n[6/8] Checking Foundry...")
    anvil_path = shutil.which("anvil")
    forge_path = shutil.which("forge")

    if not anvil_path or not forge_path:
        fail("Foundry not installed (anvil/forge missing)")
        return False, "MODE=local requires Foundry (anvil + forge) to be installed"

    ok("Foundry available")
    return True, None


def start_anvil():
    """Start Anvil local chain."""
    global anvil_process, anvil_log_file
    print("\n[7/8] Starting Anvil...")

    if anvil_process and anvil_process.poll() is None:
        warn("Anvil already running")
        return True, "Anvil already running"

    try:
        log_path = os.getenv("ANVIL_LOG_PATH", "").strip()
        stdout_target = None
        stderr_target = None
        if log_path:
            anvil_log_file = open(log_path, "a", encoding="utf-8")
            stdout_target = anvil_log_file
            stderr_target = anvil_log_file

        anvil_process = subprocess.Popen(
            [
                "anvil",
                "--port", "8545",
                "--host", "127.0.0.1",
                "--chain-id", "31337",
                "--mnemonic", "test test test test test test test test test test test junk",
                "--accounts", "10"
            ],
            stdout=stdout_target,
            stderr=stderr_target
        )
        print(f"[start.py] Anvil started (PID: {anvil_process.pid})")
        time.sleep(1)

        ok_rpc, rpc_msg = check_anvil_rpc_health()
        if not ok_rpc:
            return False, rpc_msg

        return True, None
    except FileNotFoundError:
        return False, "Anvil not found in PATH"
    except Exception as e:
        return False, f"Failed to start Anvil: {e}"

def check_anvil_rpc_health(rpc_url: str | None = None, retries: int = 8, delay: float = 0.5):
    """Verify Anvil RPC health via eth_blockNumber."""
    url = rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    for _ in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=2) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            response = json.loads(body)
            block_hex = response.get("result")
            if block_hex:
                ok(f"Anvil RPC healthy (eth_blockNumber={block_hex})")
                return True, None
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            pass
        time.sleep(delay)

    return False, f"Anvil RPC health check failed ({url})"


def parse_contract_address(output_text):
    """Parse contract address from forge output."""
    matches = re.findall(r"0x[a-fA-F0-9]{40}", output_text or "")
    return matches[-1] if matches else ""


def update_env_value(env_path, key, value):
    """Update or append a key=value pair in .env."""
    if not env_path.exists():
        return False, f".env not found: {env_path}"

    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return True, None


def deploy_contract():
    """Deploy contract with Foundry in local mode."""
    print("\n[8/8] Deploying contract...")
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY", "")
    if not private_key:
        return False, "PRIVATE_KEY not set for deployment"

    contracts_dir = Path(__file__).parent / "contracts"
    try:
        result = subprocess.run(
            [
                "forge", "script",
                "script/Deploy.s.sol",
                "--rpc-url", rpc_url,
                "--private-key", private_key,
                "--broadcast"
            ],
            cwd=str(contracts_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300
        )
    except subprocess.TimeoutExpired:
        return False, "Deployment timed out (>5 minutes)"
    except Exception as e:
        return False, f"Deployment failed: {e}"

    if result.returncode != 0:
        return False, f"Deployment failed:\n{result.stderr[:2000]}"

    contract_address = parse_contract_address(result.stdout) or parse_contract_address(result.stderr)
    if not contract_address:
        return False, "Failed to parse contract address from deployment output"

    env_path = Path(__file__).parent / "backend" / ".env"
    success, msg = update_env_value(env_path, "JURY_VOTING_CONTRACT_ADDRESS", contract_address)
    if not success:
        return False, msg

    os.environ["JURY_VOTING_CONTRACT_ADDRESS"] = contract_address
    ok(f"Contract deployed: {contract_address}")
    return True, None


def check_content():
    """检查游戏内容"""
    print("\n[9/9] 检查游戏内容...")

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
    print("=" * 60)
    print("  AI Trial Game - 环境准备与启动")
    print("=" * 60)

    errors = []
    warnings = []

    # 1. 虚拟环境（可选）
    success, msg = check_venv()
    if msg:
        warnings.append(msg)

    # 2. 依赖检查
    success, msg = check_python_deps()
    if not success:
        errors.append(msg)

    # 3. 环境配置
    success, msg = check_env_file()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.extend(msg)

    # Load .env and detect MODE
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "backend" / ".env")
    global MODE
    MODE = os.getenv("MODE", "local").lower()
    if MODE not in ["local", "sepolia"]:
        print(f"Error: Invalid MODE '{MODE}'. Must be 'local' or 'sepolia'")
        sys.exit(1)

    # 如果基础依赖有问题，停止
    if errors:
        print("\n" + "=" * 60)
        print(f"{RED}[FAIL] 环境准备失败{RESET}")
        print("=" * 60)
        for e in errors:
            print(f"\n{RED}错误:{RESET} {e}")
        sys.exit(1)

    # 4. spoon-core check
    success, msg = check_spoon_core()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.append(msg)

    # 4. LLM API
    success, msg = check_llm_api()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.append(msg)

    # 5. 服务器端口检查
    success, msg = check_server_port()
    if not success:
        errors.append(msg)
    elif msg:
        warnings.append(msg)

    # 如果端口不可用，停止
    if errors:
        print("\n" + "=" * 60)
        print(f"{RED}[FAIL] 环境准备失败{RESET}")
        print("=" * 60)
        for e in errors:
            print(f"\n{RED}错误:{RESET} {e}")
        sys.exit(1)

    # 6. Foundry 检查
    if MODE == "local":
        configure_local_accounts()
        # 6. Foundry check
        success, msg = check_foundry()
        if not success:
            errors.append(msg)
        else:
            # 6. Start Anvil
            success, msg = start_anvil()
            if not success:
                errors.append(msg)
            elif msg:
                warnings.append(msg)

            # 7. Deploy contract
            success, msg = deploy_contract()
            if not success:
                errors.append(msg)
            elif msg:
                warnings.append(msg)
    elif MODE == "sepolia":
        contract_addr = os.getenv("JURY_VOTING_CONTRACT_ADDRESS", "")
        if not contract_addr or contract_addr == "0x0000000000000000000000000000000000000000":
            errors.append("MODE=sepolia requires JURY_VOTING_CONTRACT_ADDRESS in backend/.env")
        else:
            ok(f"Using existing contract at {contract_addr}")

    if errors:
        print("\n" + "=" * 60)
        print(f"{RED}[FAIL] Environment setup failed{RESET}")
        print("=" * 60)
        for e in errors:
            print(f"\n{RED}Error:{RESET} {e}")
        cleanup_on_exit()

    # 8. Content check
    check_content()

    # 结果汇总
    print("\n" + "=" * 60)

    if errors:
        print(f"{RED}[FAIL] 环境准备失败{RESET}")
        print("=" * 60)
        for e in errors:
            print(f"\n{RED}错误:{RESET} {e}")
        cleanup_on_exit()

    if warnings:
        print(f"{YELLOW}! 环境准备完成 (有警告){RESET}")
        print("=" * 60)
        print(f"\n{YELLOW}警告:{RESET}")
        for w in warnings:
            print(f"  - {w}")
        print(f"\n{YELLOW}部分功能可能不可用，但游戏可以启动。{RESET}")
    else:
        print(f"{GREEN}[OK] 环境准备完成{RESET}")
        print("=" * 60)

    # 自动启动游戏服务器
    print(f"\n{GREEN}正在启动游戏服务器...{RESET}\n")

    # 保持 Anvil 运行，启动服务器
    # Keep Anvil running and start backend server
    backend_dir = Path(__file__).parent / "backend"
    try:
        global backend_process
        python_exec = get_python_executable()
        backend_process = subprocess.Popen(
            [python_exec, "main.py"],
            cwd=str(backend_dir)
        )
        print(f"[start.py] Backend started (PID: {backend_process.pid})")
        backend_process.wait()
    except KeyboardInterrupt:
        cleanup_on_exit()
    except Exception as e:
        print(f"{RED}启动失败: {e}{RESET}")
        cleanup_on_exit()
    finally:
        cleanup_on_exit()

if __name__ == "__main__":
    main()
