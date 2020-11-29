#!/usr/bin/python3
from bluezero import peripheral

UART_SERIVCE = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_CHARACTERISTIC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
TX_CHARACTERISTIC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'

class UartService:
    def __init__(self, onread, alias='RPi_UART'):
        self.onread = onread
        self.app = peripheral.Application()
        self.ble_uart = peripheral.Service(UART_SERIVCE, True)
        self.rx_uart = peripheral.Characteristic(RX_CHARACTERISTIC,
            ['write', 'write-without-response'], self.ble_uart)
        self.tx_uart = peripheral.Characteristic(TX_CHARACTERISTIC,
            ['notify'], self.ble_uart)
        self.rx_uart.add_write_event(self.uart_print)
        self.ble_uart.add_characteristic(self.rx_uart)
        self.ble_uart.add_characteristic(self.tx_uart)
        self.app.add_service(self.ble_uart)
        self.app.dongle.alias = alias
    def uart_print(self, data):
        value = ''.join(chr(letter) for letter in data)
        self.onread(value)
    def start(self):
        self.app.start()

######################

import argparse
import paho.mqtt.client as mqtt
from datetime import datetime

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--broker", default="127.0.0.1", help='broker host')
parser.add_argument("--port", default=1883, help='broker port')
parser.add_argument("--keepalive", default=60, help='broker keep alive')
parser.add_argument("--topic", default="f/tx", help='command topic')

def main():
    def onconnect(client, userdata, flags, rc):
        client.subscribe('#')
    def onwrite(value):
        client.publish(args.topic, value)
    def onmessage(client, userdata, msg):
        payload = msg.payload.decode('latin')
        ts = datetime.now().strftime('%H:%M:%S')
        uart.tx_uart.send_notify_event(f'{ts} {msg.topic} {payload}')
    uart = UartService(onwrite)
    client = mqtt.Client()
    client.on_connect = onconnect
    client.on_message = onmessage
    client.connect(args.broker, args.port, args.keepalive)
    client.loop_start()
    uart.start()

if __name__ == '__main__':
    # proxy ble uart to mqtt broker
    # this needs to run as root
    args = parser.parse_args()
    main()

