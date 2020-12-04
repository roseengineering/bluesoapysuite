#!/usr/bin/python3

import argparse
import paho.mqtt.client as mqtt
from datetime import datetime
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--broker", default="127.0.0.1", help='broker host')
parser.add_argument("--port", default=1883, help='broker port')
parser.add_argument("--keepalive", default=60, help='broker keep alive')
parser.add_argument("--pps-topic", default="pps", help='PPS topic')

def gen_topic(name=None):
    d = args.topic.split('/')[:-1]
    if name is not None:
        d.append(name)
    return '/'.join(d)

def on_connect(client, userdata, flags, rc):
    client.subscribe(gen_topic('#'))

def on_message(client, userdata, msg):
    payload = msg.payload.decode('latin').strip()
    if msg.topic == args.pps_topic:
        print(f'{msg.topic} {payload}')

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, args.port, args.keepalive)
    client.loop_start()
    mode = WATCH_ENABLE | WATCH_NEWSTYLE
    session = gps(mode=mode)
    for nx in session:
        if nx['class'] == 'TPV':
            mode = nx['mode']
            ts = nx.get('time')
            if ts and (mode == 2 or mode == 3):
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                client.publish(args.pps_topic, ts) 

if __name__ == '__main__':
    args = parser.parse_args()
    main()


