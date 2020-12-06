
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

  # apt

  - become: yes
    apt:
      name:
      - mosquitto

  # pip

  - become: yes
    pip:
      name:
      - gps
      - paho-mqtt

  # mqpps

{copy("mqpps.py", "/usr/local/bin/mqpps")}

  - become: yes
    copy:
      dest: /lib/systemd/system/mqpps.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqpps
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

  - become: yes
    shell: |
      sudo systemctl enable mqpps

  - become: yes
    shell: |
      sudo systemctl restart mqpps
""")


