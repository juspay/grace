#!/usr/bin/env python3
"""Verify GRACE gRPC testing setup"""

import os
import sys
from pathlib import Path
import json

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (MISSING)")
        return False

def verify_configuration():
    """Verify the configuration"""
    print("Checking GRACE gRPC Testing Setup\n")
    print("="*60)

    all_good = True

    # Check essential files
    all_good &= check_file_exists(".env.grpc", "Environment configuration")
    all_good &= check_file_exists("test_sets.json", "Test sets configuration")
    all_good &= check_file_exists("grpc_generator.py", "gRPC generator")
    all_good &= check_file_exists("grpc_executor.py", "gRPC executor")
    all_good &= check_file_exists("run_grpc_tests.py", "Test runner")

    print("\nChecking request templates:")
    request_files = [
        "grpc_requests/auth.json",
        "grpc_requests/capture.json",
        "grpc_requests/void.json",
        "grpc_requests/refund.json",
        "grpc_requests/sync.json",
        "grpc_requests/rsync.json"
    ]

    for req_file in request_files:
        all_good &= check_file_exists(req_file, f"Template: {req_file.split('/')[-1]}")

    # Check configuration values
    print("\n" + "="*60)
    print("Configuration verification:")

    if Path(".env.grpc").exists():
        with open(".env.grpc", 'r') as f:
            env_config = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_config[key.strip()] = value.strip()

        required_keys = [
            'CONNECTOR_NAME',
            'CONNECTOR_AUTH_TYPE',
            'CONNECTOR_API_KEY',
            'CONNECTOR_KEY1',
            'CARD_NUMBER',
            'CARD_CVC'
        ]

        for key in required_keys:
            if key in env_config:
                if 'CVC' in key and env_config[key] == '999':
                    print(f"⚠️  {key}: {env_config[key]} (Should be 123 for Powertranz)")
                    all_good = False
                else:
                    print(f"✓ {key}: {'*' * len(env_config[key]) if 'KEY' in key else env_config[key]}")
            else:
                print(f"✗ {key}: NOT SET")
                all_good = False

    # Check test sets
    print("\n" + "="*60)
    print("Test sets verification:")

    if Path("test_sets.json").exists():
        with open("test_sets.json", 'r') as f:
            test_sets = json.load(f)

        for i, test_set in enumerate(test_sets.get('test_sets', []), 1):
            print(f"\nTest Set {i}: {test_set.get('name', 'Unnamed')}")
            print(f"  Description: {test_set.get('description', 'No description')}")

            has_rsync = any(step.get('operation') == 'rsync'
                           for step in test_set.get('steps', []))
            if has_rsync:
                print("  ✓ Includes rsync operation for refund sync")

    # Check服务器状态
    print("\n" + "="*60)
    print("Server connectivity check:")

    try:
        import subprocess
        result = subprocess.run(
            ["grpcurl", "-plaintext", "localhost:8000", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ gRPC server is running on localhost:8000")
        else:
            print("✗ gRPC server not responding on localhost:8000")
            all_good = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Cannot verify gRPC server (grpcurl not installed or server not running)")

    print("\n" + "="*60)
    if all_good:
        print("✓ Setup verification: PASSED")
        print("\nYou can now run the tests with:")
        print("  python3 run_grpc_tests.py")
        print("  ./grace-test.sh")
    else:
        print("✗ Setup verification: FAILED")
        print("\nPlease fix the issues above before running tests.")
        sys.exit(1)

if __name__ == "__main__":
    verify_configuration()