#!/usr/bin/env python3
"""
Verification script for Local Chain Migration implementation.
Checks all critical invariants from the specification.
"""

import re
import sys
from pathlib import Path

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")
    return False

def warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")

# Expected Anvil account values from spec FR-3
EXPECTED_ACCOUNTS = {
    "PRIVATE_KEY": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "JUROR_1": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "JUROR_2": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "JUROR_3": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
    "JUROR_4": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
    "JUROR_5": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
}

EXPECTED_KEYS = [
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
]

def verify_start_py():
    """Verify start.py implementation."""
    print("\n=== Verifying start.py ===")

    start_py = Path("start.py")
    if not start_py.exists():
        return fail("start.py not found")

    content = start_py.read_text(encoding='utf-8')

    # Check 1: Signal handlers
    if "signal.signal(signal.SIGINT" in content:
        ok("Signal handlers registered")
    else:
        return fail("Signal handlers missing")

    # Check 2: cleanup_on_exit function
    if "def cleanup_on_exit" in content:
        ok("cleanup_on_exit function exists")
    else:
        return fail("cleanup_on_exit function missing")

    # Check 3: MODE configuration
    if 'MODE = os.getenv("MODE", "local")' in content:
        ok("MODE configuration present")
    else:
        return fail("MODE configuration missing")

    # Check 4: MODE validation
    if 'MODE not in ["local", "sepolia"]' in content:
        ok("MODE validation present")
    else:
        return fail("MODE validation missing")

    # Check 5: configure_local_accounts function
    if "def configure_local_accounts" in content:
        ok("configure_local_accounts function exists")

        # Verify account values
        all_correct = True
        for key, expected_value in EXPECTED_ACCOUNTS.items():
            if expected_value in content:
                ok(f"  Correct {key}")
            else:
                fail(f"  Incorrect or missing {key}")
                all_correct = False

        # Verify private keys
        for i, key in enumerate(EXPECTED_KEYS, 1):
            if key in content:
                ok(f"  Correct JUROR_{i} private key")
            else:
                fail(f"  Incorrect or missing JUROR_{i} private key")
                all_correct = False

        if not all_correct:
            return False
    else:
        return fail("configure_local_accounts function missing")

    # Check 6: start_anvil function
    if "def start_anvil" in content:
        ok("start_anvil function exists")

        # Check Anvil parameters
        if '"--port", "8545"' in content:
            ok("  Anvil port: 8545")
        else:
            fail("  Anvil port not 8545")

        if '"--host", "127.0.0.1"' in content:
            ok("  Anvil host: 127.0.0.1")
        else:
            fail("  Anvil host not 127.0.0.1")

        if '"--chain-id", "31337"' in content:
            ok("  Anvil chain-id: 31337")
        else:
            fail("  Anvil chain-id not 31337")

        if "test test test test test test test test test test test junk" in content:
            ok("  Anvil mnemonic: default")
        else:
            fail("  Anvil mnemonic not default")
    else:
        return fail("start_anvil function missing")

    # Check 7: Supervisor pattern (no os.execvp)
    if "os.execvp" in content:
        return fail("os.execvp still present (should be removed)")
    else:
        ok("os.execvp removed (supervisor pattern)")

    # Check 8: backend_process.wait()
    if "backend_process.wait()" in content:
        ok("backend_process.wait() present")
    else:
        return fail("backend_process.wait() missing")

    return True

def verify_frontend():
    """Verify frontend implementation."""
    print("\n=== Verifying Frontend ===")

    game_js = Path("frontend/js/game.js")
    index_html = Path("frontend/index.html")

    if not game_js.exists():
        return fail("frontend/js/game.js not found")

    if not index_html.exists():
        return fail("frontend/index.html not found")

    game_content = game_js.read_text(encoding='utf-8')
    html_content = index_html.read_text(encoding='utf-8')

    # Check 1: No Etherscan links
    if "sepolia.etherscan.io" in game_content or "sepolia.etherscan.io" in html_content:
        return fail("Sepolia Etherscan links still present")
    else:
        ok("Etherscan links removed")

    # Check 2: Transaction hash display
    if "class=\"tx-hash\"" in game_content:
        ok("Transaction hash display (copyable)")
    else:
        warn("Transaction hash styling missing (optional)")

    # Check 3: Animation duration (2000ms)
    if "animateProgressBar(60, 90, 2000)" in game_content:
        ok("Animation duration: 2000ms")
    else:
        # Check if it's 9000 (old value)
        if "animateProgressBar(60, 90, 9000)" in game_content:
            return fail("Animation duration still 9000ms (should be 2000ms)")
        else:
            warn("Animation duration changed but not to 2000ms")

    # Check 4: Enhanced error handling
    if "ECONNREFUSED" in game_content and "本地链连接失败" in game_content:
        ok("Enhanced error handling present")
    else:
        return fail("Enhanced error handling missing")

    # Check 5: No "Sepolia" text
    if "Sepolia" not in html_content:
        ok("No 'Sepolia' text in HTML")
    else:
        warn("'Sepolia' text still present in HTML")

    # Check 6: "本地链" text
    if "本地链" in html_content or "本地链" in game_content:
        ok("'本地链' terminology present")
    else:
        warn("'本地链' terminology missing")

    return True

def verify_env_example():
    """Verify .env.example update."""
    print("\n=== Verifying .env.example ===")

    env_example = Path("backend/.env.example")
    if not env_example.exists():
        return fail("backend/.env.example not found")

    content = env_example.read_text(encoding='utf-8')

    # Check MODE documentation
    if "MODE=local" in content:
        ok("MODE=local documented")
    else:
        return fail("MODE=local not documented")

    if "Auto-configured" in content:
        ok("Auto-configuration documented")
    else:
        warn("Auto-configuration not clearly documented")

    if "MODE=sepolia" in content:
        ok("MODE=sepolia documented")
    else:
        warn("MODE=sepolia not documented")

    return True

def main():
    """Run all verifications."""
    print("=" * 60)
    print("Local Chain Migration - Implementation Verification")
    print("=" * 60)

    results = []

    results.append(verify_start_py())
    results.append(verify_frontend())
    results.append(verify_env_example())

    print("\n" + "=" * 60)
    if all(results):
        print(f"{GREEN}✓ All verifications passed!{RESET}")
        print("=" * 60)
        print("\nReady for testing:")
        print("  1. python start.py")
        print("  2. Visit http://localhost:8080/game")
        print("  3. Test voting flow")
        print("  4. Test Ctrl+C cleanup")
        return 0
    else:
        print(f"{RED}✗ Some verifications failed{RESET}")
        print("=" * 60)
        print("\nPlease review the failures above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
