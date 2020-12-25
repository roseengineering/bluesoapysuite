
import os, subprocess 

def copy(filename, path):
    command = f"base64 -w60 {filename} | sed 's/^/        /'"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    buf = proc.stdout.read().decode()
    proc.wait()
    return f"""\
  - become: yes
    copy:
      mode: 0755
      dest: {path}
      content: !!binary |\n{buf}
"""

print(f"""\
---
  # code

  - become: yes
    pip:
      name:
      - paho-mqtt

{copy("mqclient.py", "/usr/local/bin/mqclient")}

""")


