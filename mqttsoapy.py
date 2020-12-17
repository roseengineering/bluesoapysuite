
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
  - set_fact:
      fs_path: "{{{{ fs_path | default('/srv') }}}}"

  # apt

  - become: yes
    apt:
      name:
      - mosquitto

  # pip

  - become: yes
    pip:
      name:
      - paho-mqtt

  # code

{copy("mqsoapy.py", "/usr/local/bin/mqsoapy")}
{copy("mqclient.py", "/usr/local/bin/mqclient")}

  # output directory

  - become: yes
    file: path={{{{ fs_path }}}} state=directory owner={{{{ user }}}} group={{{{ user }}}}

  - become: yes
    copy:
      dest: /lib/systemd/system/mqsoapy.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqsoapy --rtltcp --pause --output {{{{ fs_path }}}}/out
        # WorkingDirectory={{{{ fs_path }}}}
        User={os.environ['USER']}
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

  - become: yes
    shell: |
      sudo systemctl enable mqsoapy
      sudo systemctl restart mqsoapy

""")


