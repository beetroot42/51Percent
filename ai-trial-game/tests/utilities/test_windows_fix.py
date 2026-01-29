#!/usr/bin/env python3
"""Test Windows binding behavior."""

import socket


def test_bind():
    """Test port binding with Windows permissions."""
    print("Testing Windows port binding\n")

    print("1) Bind 127.0.0.1:8080...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 8080))
        sock.close()
        print("   OK: bound without admin permissions\n")
    except OSError as e:
        print(f"   ERROR: {e}\n")

    print("2) Bind 0.0.0.0:8080...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", 8080))
        sock.close()
        print("   OK: bound with admin permissions\n")
    except OSError as e:
        if e.errno == 10013:
            print("   ERROR: permission denied (WinError 10013)")
            print("   Expected: 0.0.0.0 requires admin on Windows\n")
        else:
            print(f"   ERROR: {e}\n")

    print("Conclusion:")
    print("  - Use 127.0.0.1 to avoid admin permissions")
    print("  - backend/.env should set SERVER_HOST=127.0.0.1")


if __name__ == "__main__":
    test_bind()
