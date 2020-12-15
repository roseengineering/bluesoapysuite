#!/usr/bin/python3

import os, sys, time
import socket
import struct
import argparse
import numpy as np
import paho.mqtt.client as mqtt
import SoapySDR
from datetime import datetime
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32

restart_seconds = 10

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# broker
parser.add_argument("--broker", default="127.0.0.1", help='broker host')
parser.add_argument("--broker-port", default=1883, type=int, help='broker port')
parser.add_argument("--broker-keepalive", default=60, type=int, help='broker keepalive seconds')
parser.add_argument("--topic", default="f/tx", help='mqtt topic for command')
parser.add_argument("--pps-topic", default="pps", help='mqtt topic for gps pps time')
parser.add_argument("--nobroker", action="store_true", help="disable mqtt broker")
parser.add_argument("--refresh-pps", default=10, type=int, help='pps refresh in seconds')

# soapy
parser.add_argument("--driver", help='name of driver')
parser.add_argument("--packet-size", default=1024, type=int, help='packet size')
parser.add_argument("--freq", type=np.float, help="center frequency in hertz")
parser.add_argument("--rate", type=np.float, help="sample rate in hertz")
parser.add_argument("--gain", type=np.float, help="front end gain in dB")
parser.add_argument("--agc", action="store_true", help="enable AGC")

# soapy argString
parser.add_argument("--direct-samp", help="0=off, 1 or i=I, 2 or q=Q channel")
parser.add_argument("--iq-swap", action="store_true", help="swap IQ signals")
parser.add_argument("--biastee", action="store_true", help="enable bias tee")
parser.add_argument("--digital-agc", action="store_true", help="enable digital AGC")
parser.add_argument("--offset-tune", action="store_true", help="enable offset tune")

# other
parser.add_argument("--output", default="out", help="write CF32 samples to file")
parser.add_argument("--nowave", action="store_true", help="disable WAV header")
parser.add_argument("--pause", action="store_true", help="pause output")

# peak meter
parser.add_argument("--refresh", default=5, type=int, help="peak meter refresh in seconds")
parser.add_argument("--meter", action="store_true", help="enable console peak meter")
parser.add_argument("--dumb", action="store_true", help="enable dumb terminal console")
 
# tcp server
parser.add_argument("--host", default="127.0.0.1", help="CF32 tcp server host address")
parser.add_argument("--port", type=int, default=1234, help="CF32 tcp server port address")
parser.add_argument("--rtltcp", action="store_true", help="enable CU8 rtltcp server mode")
parser.add_argument("--noserver", action="store_true", help="disable tcp server")



def gen_topic(name=None):
    d = args.topic.split('/')[:-1]
    if name is not None:
        d.append(name)
    return '/'.join(d)


def to_float(param):
    try:
        return float(param)
    except ValueError:
        pass

###

def on_info(param):
    chan = 0
    for r in radio.getSampleRateRange(SOAPY_SDR_RX, chan):
       payload = 'rate: {:.3f} KHz'.format(r.minimum() / 1e3)
       info(payload)
    for r in radio.getFrequencyRange(SOAPY_SDR_RX, chan):
       payload = 'freq: {:.6f} - {:.6f} MHz'.format(
           r.minimum() / 1e6, r.maximum() / 1e6)
       info(payload)
    r = radio.getGainRange(SOAPY_SDR_RX, chan)
    payload = 'gain: {:.2f} - {:.2f} dB'.format(r.minimum(), r.maximum())
    info(payload)


def on_fatal(param):
    global fatal
    if param.lower() == "true":
        fatal = True
        info('fatal killing')
    else:
        info('bad fatal command')


def on_kill(param):
    global killed
    if param.lower() == "true":
        killed = True
        info('killing stream')
    else:
        info('bad kill command')


def on_pause(param):
    global paused
    if param:
        paused = param.lower() == "true"
    broker.publish(gen_topic("pause"), 'on' if paused else 'off')


def on_rate(param):
    global rate
    if param:
        param = to_float(param)
        if param is None:
            info('bad sample rate command')
        else:
            radio.setSampleRate(SOAPY_SDR_RX, 0, param)
    rate = radio.getSampleRate(SOAPY_SDR_RX, 0)
    broker.publish(gen_topic("rate"), f'{rate/1e3:.3f} KHz')


def on_freq(param):
    if param:
        param = to_float(param)
        if param is None:
            info('bad frequency command')
        else:
            radio.setFrequency(SOAPY_SDR_RX, 0, param)
    freq = radio.getFrequency(SOAPY_SDR_RX, 0)
    broker.publish(gen_topic("freq"), f'{freq/1e6:.6f} MHz')


def on_gain(param):
    if param:
        param = to_float(param)
        if param is None:
            info('bad gain command')
        else:
            radio.setGain(SOAPY_SDR_RX, 0, param)
    gain = radio.getGain(SOAPY_SDR_RX, 0)
    broker.publish(gen_topic("gain"), f'{gain:.3g} dB')


def on_auto(param):
    if param:
        radio.setGainMode(SOAPY_SDR_RX, 0, param.lower() == "true")
    agc = radio.getGainMode(SOAPY_SDR_RX, 0)
    broker.publish(gen_topic("agc"), 'on' if agc else 'off')


def on_setting(key, param):
    if param:
        radio.writeSetting(key, param)
    val = radio.readSetting(key)
    broker.publish(gen_topic(key), str(val))


def on_pps(ts):
    if timefile and not paused:
        sec = samples_total / rate
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        if dt.second % args.refesh_pps == 0:
            info(ts)
        timefile.write(f"{sec:.3f}\t{sec:.3f}\t{ts}\n")
        timefile.flush()


def on_message(client, userdata, msg):
    payload = msg.payload.decode('latin').strip()
    try:
        if payload and msg.topic == args.pps_topic:
            on_pps(payload)
        if payload and msg.topic == args.topic:
            cmd, _, param = payload.partition(' ') 
            param = param.strip()
            if cmd == 'i':
                on_info(param)
            elif cmd == 'p':
                on_pause(param)
            elif cmd == 'g':
                on_gain(param)
            elif cmd == 'a':
                on_auto(param)
            elif cmd == 'r':
                on_rate(param)
            elif cmd == 'f':
                on_freq(param)
            elif cmd == 'k':
                on_kill(param)
            elif cmd == 'K':
                on_fatal(param)
            elif cmd == 'ds':
                if param.lower() == "i": param = "1"
                if param.lower() == "q": param = "2"
                on_setting("direct_samp", param)
            elif cmd == 'iq':
                on_setting("iq_swap", param)
            elif cmd == 'bt':
                on_setting("biastee", param)
            elif cmd == 'da':
                on_setting("digital_agc", param)
            elif cmd == 'ot':
                on_setting("offset_tune", param)
            else:
                info('unknown command')
    except Exception as e:
        info(f"Exception on_message(): {e}")


def on_connect(client, userdata, flags, rc):
    client.subscribe(gen_topic('#'))
    client.subscribe(args.pps_topic)


###############3


def info(payload):
    print(payload, file=sys.stderr)
    if broker:
        broker.publish(gen_topic("info"), payload)


def log_handler(log_level, log_message):
    if broker:
        broker.publish(gen_topic("log"), log_message)


def wav_header(rate, channels=2, sample_bytes=4):
    rate = int(rate)
    data_id = b'data'
    data_size = 0x80000000
    riff_id = b'RIFF'
    riff_format = b'WAVE'
    fmt_id = b'fmt '
    fmt_size = 16
    fmt_format = 3    # IEEE_FLOAT
    buf = struct.pack('<4sI4s', riff_id, data_size + 20 + fmt_size, riff_format)
    buf += struct.pack('<4sIHH', fmt_id, fmt_size, fmt_format, channels)
    buf += struct.pack('<IIHH',
        rate,                           # 32-bit
        rate * channels * sample_bytes, # 32-bit
        channels * sample_bytes,
        sample_bytes * 8)
    buf += struct.pack('<4sI', data_id, data_size)
    return buf


def radio_connect():
    global radio
    drivers = [ d['driver'] for d in SoapySDR.Device.enumerate() ]
    info(f"Found drivers: {drivers}")
    kw = {}
    if args.driver:
        kw['driver'] = args.driver
    info(f"Passing the following arguments: {kw}")
    radio = SoapySDR.Device(kw)


def radio_settings():
    info(f"Initializing radio settings")
    if args.freq:
        radio.setFrequency(SOAPY_SDR_RX, 0, args.freq)
    if args.rate:
        radio.setSampleRate(SOAPY_SDR_RX, 0, args.rate)
    radio.setGainMode(SOAPY_SDR_RX, 0, args.agc);
    if args.gain:
        radio.setGain(SOAPY_SDR_RX, 0, args.gain)
    if args.direct_samp:
        param = args.direct_samp
        if param.lower() == "i": param = "1"
        if param.lower() == "q": param = "2"
        radio.writeSetting("direct_samp", param)
    if args.iq_swap:
        radio.writeSetting("iq_swap", "true")
    if args.biastee:
        radio.writeSetting("biastee", "true")
    if args.digital_agc:
        radio.writeSetting("digital_agc", "true")
    if args.digital_agc:
        radio.writeSetting("offset_tune", "true")


def main_init():
    global paused, killed, fatal
    killed = False
    fatal = False
    paused = args.pause


def broker_init():
    global broker, timefile
    timefile = None
    broker = None
    if not args.nobroker:
        info(f"Connecting to broker: {args.broker}")
        broker = mqtt.Client()
        broker.on_connect = on_connect
        broker.on_message = on_message
        broker.connect(args.broker, args.broker_port, args.broker_keepalive)
        broker.loop_start()


def main():
    broker_init()
    SoapySDR.registerLogHandler(log_handler)
    initialized= False
    while True:
        try:
            main_init()
            radio_connect()
            if not initialized:
                radio_settings()
            initialized = True
            radio_start()
        except Exception as e:
            info(f"Exception main(): {e}")
            time.sleep(restart_seconds)


def close_file(f, name):
    if f:
        info(f"Closing {name} file.")
        f.close()


def open_files():
    dt = datetime.utcnow()
    ts = dt.strftime('%y%m%d_%H%M%S')
    freq = radio.getFrequency(SOAPY_SDR_RX, 0)
    basename = f"{args.output}_{ts}Z_{freq/1e6:.6f}MHz"
    ext = 'txt'
    filename = f"{basename}.{ext}"
    info(f"Opening {filename} for gps pps time")
    timefile = open(filename, "w")
    ext = 'raw' if args.nowave else 'wav'
    filename = f"{basename}.{ext}"
    info(f"Opening {filename} for audio")
    audiofile = open(filename, "wb")
    if not args.nowave:
        audiofile.write(wav_header(rate=rate))
    return audiofile, timefile


def close_stream(stream):
    info(f"Closing radio stream.")
    radio.deactivateStream(stream) 
    radio.closeStream(stream)


def radio_peak(peak_level):
    db = "{:.1f} dB".format(20 * np.log10(peak_level + 1e-99))
    if args.meter:
        buf = f"{db}\n" if args.dumb else f"\33[2K{db:>9s}\r"
        print(buf, end="", file=sys.stderr)
    if broker:
        broker.publish(gen_topic("peak"), db)


###############3

sock_list = []
sock_server= None

def open_conn(self, sock, client_address):
    sock_list.append(sock)


def close_conn(sock):
    sock_list.remove(sock)
    sock.close()


def tcp_server(data):
    if args.rtlsdr:
        data = (data * 128 + 128).astype('B')
    readable, writable, exceptional = select.select(sock_list, sock_list, sock_list, 0)
    for sock in outsocks:
        if sock in exceptional:
            close_conn(sock)
    for sock in outsocks:
        if sock in writable:
            try:
                sock.sendall(data)
            except OSError:
                close_conn(sock)
    for sock in insocks:
        if sock in readable:
            if sock == sock_server:
                conn, client_address = sock.accept()
                open_conn(conn, client_address)
                if not args.float:
                    tuner_number = 5 # R820T
                    tuner_gains = 29 # R820T
                    dongle_info = struct.pack('>4sII', b'RTL0', tuner_number, tuner_gains)
                    conn.sendall(dongle_info)
            else:
                sock.recv(4096)


def init_server(self):
    global sock_server, sock_list
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    sock.listen()
    sock_list = [ sock ]
    sock_server = sock


def radio_start():
    global rate, timefile, samples_total
    if not args.noserver: 
        init_server()
    rate = radio.getSampleRate(SOAPY_SDR_RX, 0)
    data = np.array([0] * args.packet_size * 2, np.float32)
    stream = radio.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    radio.activateStream(stream) 
    samples_total = 0
    peak_level = 0
    sample_num = 0
    outfile = None
    try:
        while not killed and not fatal:
            radio.readStream(stream, [data], args.packet_size)
            if not paused:
                if not outfile:
                    outfile, timefile = open_files()
                samples_total += args.packet_size
                outfile.write(data)
            if not args.noserver:
                tcp_server(data)

            # peak meter
            peak_level = max(peak_level, abs(data.min()), abs(data.max()))
            sample_num += args.packet_size
            if sample_num > rate * args.refresh:
                radio_peak(peak_level)
                peak_level = 0
                sample_num = 0
    except (KeyboardInterrupt, SystemError) as e:
        info(f"Exception radio_start(): {e}")
    close_file(outfile, "audio")
    timefile = close_file(timefile, "time")
    close_stream(stream)
    if fatal:
        info("Fatal command given, killing process")
        sys.exit(1)


if __name__ == '__main__':
    args = parser.parse_args()
    main()

