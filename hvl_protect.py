# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# =============================================================================
import os

HEADER = """# =============================================================================
# (c) 2026 HEALY VECTOR LABS. ALL RIGHTS RESERVED.
# This source code is the proprietary property of Michael Healy.
# Unauthorized reproduction, distribution, or reverse-engineering is strictly
# prohibited. This file is part of the VERITAS Auditor / FASE Engine.
# =============================================================================
"""

def protect_files():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py") and file != "hvl_protect.py":
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                if "(c) 2026 HEALY VECTOR LABS" not in content:
                    print(f"[+] Shielding: {filepath}")
                    with open(filepath, 'w') as f:
                        f.write(HEADER + "\n" + content)
                else:
                    print(f"[-] Already Protected: {filepath}")

if __name__ == "__main__":
    protect_files()

