
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

  # output directory

  - become: yes
    file: path={{{{ fs_path }}}} state=directory owner={{{{ user }}}} group={{{{ user }}}}

  # bluezero / mqtt

  - become: yes
    apt:
      name:
      - python3-dbus

  - become: yes
    pip:
      name:
      - bluezero
      - paho-mqtt

  - become: yes
    copy:
      dest: /etc/dbus-1/system.d/ukBaz.bluezero.conf 
      content: |
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE busconfig PUBLIC 
         "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
         "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
        <busconfig>
          <policy context="default">
            <allow own="ukBaz.bluezero"/>
            <allow send_destination="ukBaz.bluezero"
                   send_interface="org.freedesktop.DBus.Introspectable"/>
            <allow send_type="method_call" log="true"/>
          </policy>
        </busconfig>

  # bluesoapy

{copy("mqproxy.py", "/usr/local/bin/mqproxy")}
{copy("mqsoapy.py", "/usr/local/bin/mqsoapy")}
{copy("mqpps.py", "/usr/local/bin/mqpps")}
{copy("mqclient.py", "/usr/local/bin/mqclient")}

  - become: yes
    copy:
      dest: /lib/systemd/system/mqproxy.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqproxy
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

  - become: yes
    copy:
      dest: /lib/systemd/system/mqsoapy.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqsoapy --pause --output {{{{ fs_path }}}}/out
        # WorkingDirectory={{{{ fs_path }}}}
        User={os.environ['USER']}
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

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
      sudo systemctl enable mqproxy
      sudo systemctl enable mqsoapy
      sudo systemctl enable mqpps

  - become: yes
    shell: |
      sudo systemctl restart mqproxy
      sudo systemctl restart mqsoapy
      sudo systemctl restart mqpps
""")


