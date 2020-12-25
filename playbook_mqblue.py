
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
  # ble

  - become: yes
    apt:
      name:
      - python3-dbus

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

  # code

  - become: yes
    pip:
      name:
      - paho-mqtt
      - bluezero

{copy("mqblue.py", "/usr/local/bin/mqblue")}

  # output directory

  - become: yes
    copy:
      dest: /lib/systemd/system/mqblue.service
      content: |
        [Service]
        ExecStart=/usr/bin/python3 -u /usr/local/bin/mqblue
        Restart=on-failure
        RestartSec=10s
        [Install]
        WantedBy=multi-user.target

  - become: yes
    shell: |
      sudo systemctl enable mqblue
      sudo systemctl restart mqblue

""")


