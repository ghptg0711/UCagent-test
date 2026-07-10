import subprocess
import sys

SUDO_PASSWORD = "1234"

def run_wsl_command(cmd, description, need_sudo=False):
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    if need_sudo:
        full_cmd = ["wsl", "-d", "Ubuntu", "bash", "-c", f"echo {SUDO_PASSWORD} | sudo -S {cmd}"]
    else:
        full_cmd = ["wsl", "-d", "Ubuntu", "bash", "-c", cmd]
    
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    print("STDOUT:", result.stdout[:3000] if len(result.stdout) > 3000 else result.stdout)
    print("STDERR:", result.stderr[:3000] if len(result.stderr) > 3000 else result.stderr)
    
    return result.returncode == 0, result.stdout, result.stderr

success, stdout, stderr = run_wsl_command("apt-get update -y", "Update apt", need_sudo=True)
if not success:
    print("Failed to update apt")
    sys.exit(1)

success, stdout, stderr = run_wsl_command("apt-get install -y openjdk-11-jdk make gcc g++ curl", "Install dependencies", need_sudo=True)
if not success:
    print("Failed to install dependencies")
    sys.exit(1)

success, stdout, stderr = run_wsl_command("java -version", "Check Java")

success, stdout, stderr = run_wsl_command("curl -L https://github.com/com-lihaoyi/mill/releases/download/0.11.6/0.11.6 > /tmp/mill && chmod +x /tmp/mill", "Download Mill")
if success:
    run_wsl_command("mv /tmp/mill /usr/local/bin/mill", "Install Mill", need_sudo=True)

success, stdout, stderr = run_wsl_command("mill -version", "Verify Mill")

print("\nStarting NutShell compilation (this may take several minutes)...")
success, stdout, stderr = run_wsl_command(
    "cd /mnt/d/UCagent/NutShell && export MILL_JVM_OPTS='-Xmx4G -Xss256m' && make verilog 2>&1",
    "Compile NutShell to Verilog"
)

if success:
    print("\n" + "="*60)
    print("NutShell compiled successfully!")
    print("="*60)
    run_wsl_command("ls -la /mnt/d/UCagent/NutShell/build/rtl/", "List build directory")
else:
    print("\nCompilation failed.")
    sys.exit(1)