#!/usr/bin/python3

import sys
import argparse
import paho.mqtt.client as mqtt

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--broker", default="127.0.0.1", help='broker host')
parser.add_argument("--port", default=1883, help='broker port')
parser.add_argument("--keepalive", default=60, help='broker keep alive')
parser.add_argument("--topic", default="f/tx", help='command topic')

def on_connect(client, userdata, flags, rc):
    client.subscribe("#")

def on_message(client, userdata, msg):
    print(msg.topic + " " + msg.payload.decode('latin'))

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, args.port, args.keepalive)
    client.loop_start()
    while True:
        line = next(sys.stdin).rstrip()
        client.publish(args.topic, line) 

if __name__ == '__main__':
    args = parser.parse_args()
    main()


