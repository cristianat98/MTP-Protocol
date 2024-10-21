import RPi.GPIO as GPIO
from lib_nrf24 import *
import time
import spidev

GPIO.setmode(GPIO.BCM)

pipes = [[0xe7,0xe7,0xe7,0xe7,0xe7], [0xc2,0xc2,0xc2,0xc2,0xc2]]

radio = NRF24(GPIO, spidev.SpiDev())
radio.begin(0,17)
radio.setPayloadSize(32)
radio.setChannel(0x60)

radio.setDataRate(NRF24.BR_2MBPS)
radio.setPALevel(NRF24.PA_HIGH)
radio.setAutoAck(True)
radio.enableDynamicPayloads()
radio.enableAckPayload()

radio.openWritingPipe(pipes[1])
radio.printDetails()


def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

filename = "text.txt"

file = open(filename, "rb")
strF = file.read()
buf=list(chunkstring(strF,31))
print(len(buf))
for k,p in enumerate(buf):
    print(type(p))
    ack = False
    print(p)
    while not ack:
        sent = radio.write(bytearray(p))
        if sent:
            print(sent)
           # while not radio.isAckPayloadAvailable():
            #    ack= False
            ack = True
            print('hola')
        time.sleep(1)
radio.write([1 for _ in range(32)])
print("Done")
