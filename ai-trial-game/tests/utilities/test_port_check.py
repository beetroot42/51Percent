#!/usr/bin/env python3
"""Test port availability checks."""

import socket


def test_port_check():
    """Check if port 5000 is available."""
    server_port = 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", server_port))
        sock.close()
        print(f"OK: port {server_port} available")
        return True
    except OSError as e:
        sock.close()
        if e.errno in (98, 10048):
            print(f"ERROR: port {server_port} in use")
            print(f"  Error code: {e.errno}")
            print(f"  Error: {e}")

            # Attempt to find the occupying process
            import subprocess
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{server_port}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    print(f"  PID(s): {', '.join(pids)}")
                else:
                    print("  No process information found")
            except FileNotFoundError:
                print("  lsof not available")
            except Exception as err:
                print(f"  Failed to find process: {err}")

            return False
        else:
            print(f"ERROR: port check failed: {e}")
            return False


if __name__ == "__main__":
    print("Checking port 5000...\n")
    test_port_check()
