
import subprocess 


def run(command, language=""):
    proc = subprocess.Popen("PYTHONPATH=. " + command, shell=True, stdout=subprocess.PIPE)
    buf = proc.stdout.read().decode()
    proc.wait()
    return f"""
```{language}
$ {command}
{buf}\
```
"""


print(f"""\
![gobox](res/gobox.jpg)

This repo contains a MQTT controlled SDR radio client.
Instead of using a GUI or the command line to communicate
with your SDR radio, commands and status messages are sent over MQTT.

The radio client program itself is quite simple.  It
is a Python program that uses the SoapySDR library to capture the SDR radio
stream and write the result to a file as either
a wav sound file or a raw file.

A TCP/network server is also provided for listening to
the stream.  In addition a peak dBFS reading is sent to the 
MQTT queue.  This way the radio levels can
be checked and the gain of the radio adjusted
using the radio's MQTT control (topic) channel. 

The radio client supports the following commands
over the control channel:

```
i          # probe detailed radio device information
a true     # enable or disable automatic gain control
g xxx.x    # set gain of the radio
r xxxxx    # set the sampling rate of the radio in Hertz
f xxxxx    # set the frequency of the radio in Hertz

p true     # pause or unpause the stream
k true     # kill the current stream and start a new one
K true     # kill the application itself with an exit code of 1

(see https://github.com/pothosware/SoapyRTLSDR/blob/master/Settings.cpp)
ds [0|1|2] # set IQ or direct sampling mode
iq true    # enable IQ signal swap
bt true    # enable bias tee 
da true    # enable digital agc
ot true    # enable offset tune
```

If you want to listen to the captured
stream or to see a waterfall of it, the assumption
is that you would use a third party radio client to
read the output file as it is writing - either from 
the computer hosting the client or over a network 
file server.

That said the intent of the radio client is for unattended
operation, with the MQTT queue serving to both
send commands to it and for receiving status reports from
it.  The name of the radio client application is "mqsoapy".



{run("python3 mqsoapy.py --help")}

In addition the radio supports the reception of GPS PPS signals
over a MQTT topic subscription.   Anytime a message is received
over the PPS topic the radio client writes out an Audacity formatted
label to a text file with the same name as the sound file.
In this way the sound file can be kept in sync with GPS time.
The name of the application that publishes the PPS signal
to the MQTT is "mqpps".  The program listens to the gpsd socket
on your computer and publishes the GPS time over the given
MQTT topic whenever a full "TPV" message is received from
the satellite(s).

{run("python3 mqpps.py --help")}

To communicate over the MQTT queue and send control commands
to radio client as well as receive status messages from the radio,
an application named "mqclient" is provided.  Any
line typed in the application gets sent over the MQTT topic that
serves as the radio client's control channel.

{run("python3 mqclient.py --help")}

But what if you do not have a network?  What if you are
outside without a LAN gathering radio signals?  For this, another
application is provided called "mqproxy".  This application proxies
Bluetooth signals from your phone, say, to and from 
the MQTT queue, thereby letting you control the radio client 
from your phone.  The BLE-MQTT proxy app uses the "BLE UART" device standard
to do this.
Any line sent over a "BLE UART" bluetooth connection is relayed to the
MQTT radio control topic.  And all messages received over the 
MQTT queue are sent back.  There are two phone apps I know of
that support communication over the "BLE UART" standard.  They are
nRF UART and Bluefruit LE Connect.

{run("python3 mqblue.py --help")}

Lastly to install the suite of programs provided here the repo
includes three ansible playbook for installing the suite on
the Raspberry Pi. 
""")



