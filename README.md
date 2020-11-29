This repo contains a MQTT controlled SDR radio client.
Instead of using a GUI or the command line the
commands to radio are over MQTT.

The radio client program itself is quite simple.  It 
uses the SoapySDR client to capture the SDR radio
stream and write the result to a file as either
a wav sound file or a raw file.

There is no TCP/network server port provided to monitor
the stream.  Only a peak dBFS reading is sent to
the MQTT queue.  This way the radio levels can
be checked and the gain of the radio adjusted
using the radio's MQTT control (topic) channel. 

If however you want to listen to the captured
stream or to see a waterfall of it, the assumption
is that you would use a third party radio client to
read the output file as it is writing - either from 
the computer hosting the client or over a network 
file server.

That said the intent of the radio client is for unattended
operation, with the MQTT queue serving to both
send commands to it and for receiving status reports from
it.  The name of the radio client application is "mqsoapy".


```bash
$ python3 mqsoapy.py --help
usage: mqsoapy.py [-h] [--broker BROKER] [--port PORT] [--keepalive KEEPALIVE]
                  [--topic TOPIC] [--pps-topic PPS_TOPIC] [--driver DRIVER]
                  [--packet-size PACKET_SIZE] [--freq FREQ] [--rate RATE]
                  [--gain GAIN] [--agc AGC] [--nobroker] [--dumb]
                  [--output OUTPUT] [--nowave] [--meter] [--pause]
                  [--refresh REFRESH] [--direct-samp DIRECT_SAMP] [--iq-swap]
                  [--biastee] [--digital-agc] [--offset-tune]

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       broker host (default: 127.0.0.1)
  --port PORT           broker port (default: 1883)
  --keepalive KEEPALIVE
                        broker keepalive in seconds (default: 60)
  --topic TOPIC         mqtt topic for command (default: f/tx)
  --pps-topic PPS_TOPIC
                        mqtt topic for gps time (default: pps)
  --driver DRIVER       name of driver (default: None)
  --packet-size PACKET_SIZE
                        packet size (default: 1024)
  --freq FREQ           center frequency in hertz (default: None)
  --rate RATE           sample rate in hertz (default: None)
  --gain GAIN           front end gain in dB (default: None)
  --agc AGC             0=disable, 1=enable AGC (default: None)
  --nobroker            disable mqtt broker (default: False)
  --dumb                dumb terminal (default: False)
  --output OUTPUT       write CF32 samples to file (default: out)
  --nowave              disable WAV header (default: False)
  --meter               enable peak meter (default: False)
  --pause               pause output (default: False)
  --refresh REFRESH     peak meter refresh in seconds (default: 5)
  --direct-samp DIRECT_SAMP
                        0=off, 1=I, 2=Q channel (default: None)
  --iq-swap             swap IQ signals (default: False)
  --biastee             enable bias tee (default: False)
  --digital-agc         enable digital AGC (default: False)
  --offset-tune         enable offset tune (default: False)
```


In addition the radio supports the reception of GPS PPS signals
over a MQTT topic subscription.   Anytime a message is received
over the PPS topic the radio client writes out a audacity formatted
label to a text file with the same name as the sound file.
In this way the sound file can be kept in sync with GPS time.
The name of the application that publishes the PPS signal
to the MQTT is "mqpps".


```bash
$ python3 mqpps.py --help
usage: mqpps.py [-h] [--broker BROKER] [--port PORT] [--keepalive KEEPALIVE]
                [--topic TOPIC] [--interval INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       broker host
  --port PORT           broker port
  --keepalive KEEPALIVE
                        broker keep alive
  --topic TOPIC         command topic
  --interval INTERVAL   publish interval in seconds
```


To communicate over the MQTT queue and send control commands
to radio client as well as receive status messages from the radio,
a application named "mqclient" is also provided.  Any
line typed in the application get sent over the MQTT topic that
serves as the radio client's control channel.


```bash
$ python3 mqclient.py --help
usage: mqclient.py [-h] [--broker BROKER] [--port PORT]
                   [--keepalive KEEPALIVE] [--topic TOPIC]

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       broker host
  --port PORT           broker port
  --keepalive KEEPALIVE
                        broker keep alive
  --topic TOPIC         command topic
```


But what if you do not have a network?  What if you are
outside without a LAN gathering radio signals?  So there another
application proved called "mqproxy".  This application proxies
Bluetooth signals from your phone, say, to and from 
the MQTT queue.  Thereby letting you control the radio client 
from your phone.  mqproxy using the BLE uart device standard.
Any line sent over a BLE uart connection is relayed to the
MQTT radio control topic.  And all messages received over the 
MQTT queue are sent back.  There are two phone apps I know
that support communication over BLE uart.  They are
nRF UART and the Bluefruit LE Connect apps.


```bash
$ python3 mqproxy.py --help
usage: mqproxy.py [-h] [--broker BROKER] [--port PORT] [--keepalive KEEPALIVE]
                  [--topic TOPIC]

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       broker host (default: 127.0.0.1)
  --port PORT           broker port (default: 1883)
  --keepalive KEEPALIVE
                        broker keep alive (default: 60)
  --topic TOPIC         command topic (default: f/tx)
```


Lastly to install the suite of programs provided here the repo
includes the ansible playbook I use to install the suite on
my Raspberry Pi.  The playbook is called "bluesoap.yml".  The
playbook itself is generated by running the python script bluesoap.py.
