#!/usr/bin/env python3
"""
Dependency Conflict Checker for OriginFD
Validates that all pinned dependencies are compatible before deployment.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def check_requirements_file(requirements_path):
    """Check if requirements file can be resolved without conflicts."""
    print(f"[CHECK] Checking {requirements_path}...")

    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_env"

        try:
            # Create virtual environment
            print("  [VENV] Creating test virtual environment...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True, capture_output=True)

            # Get pip path
            if sys.platform == "win32":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"

            # Upgrade pip
            subprocess.run([
                str(pip_path), "install", "--upgrade", "pip"
            ], check=True, capture_output=True)

            # Try to install requirements
            print("  [INSTALL] Installing requirements...")
            result = subprocess.run([
                str(pip_path), "install", "-r", requirements_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("  [SUCCESS] All dependencies resolve successfully!")

                # Run pip check for additional validation
                check_result = subprocess.run([
                    str(pip_path), "check"
                ], capture_output=True, text=True)

                if check_result.returncode == 0:
                    print("  [SUCCESS] No dependency conflicts found!")
                    return True
                else:
                    print("  [ERROR] Dependency conflicts found:")
                    print(check_result.stdout)
                    return False
            else:
                print("  [ERROR] Failed to install requirements:")
                print(result.stderr)
                return False

        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Error during dependency check: {e}")
            return False

def check_all_requirements():
    """Check all requirements files in the project."""
    project_root = Path(__file__).parent.parent
    requirements_files = [
        project_root / "requirements.txt",
        project_root / "services" / "api" / "requirements.txt",
        project_root / "services" / "orchestrator" / "requirements.txt",
        project_root / "services" / "workers" / "requirements.txt"
    ]

    print("OriginFD Dependency Conflict Checker")
    print("=" * 50)

    all_passed = True

    for req_file in requirements_files:
        if req_file.exists():
            success = check_requirements_file(req_file)
            all_passed = all_passed and success
            print()
        else:
            print(f"[WARN] {req_file} not found, skipping...")

    if all_passed:
        print("[SUCCESS] All dependency checks passed!")
        return 0
    else:
        print("[FAIL] Some dependency checks failed!")
        return 1

if __name__ == "__main__":
    exit_code = check_all_requirements()
    sys.exit(exit_code)
