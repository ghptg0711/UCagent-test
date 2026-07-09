import subprocess
import sys

command = [
    "wsl",
    "-d", "Ubuntu",
    "bash", "-c",
    "cd /mnt/d/UCagent/NutShell && echo 'Checking mill and java...' && which mill && java -version && echo '=== Running verilog generation ===' && make verilog"
]

print(f"Running: {' '.join(command)}")
result = subprocess.run(command, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
sys.exit(result.returncode)