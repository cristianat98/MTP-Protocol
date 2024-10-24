import time
import math
from RF24 import RF24, RF24_PA_LOW, RF24_DRIVER
import struct
from typing import List
import os

SIZE = 32  #MAX PAYLOAD SIZE
HEADER_SIZE = 2
PAYLOAD_SIZE = SIZE - HEADER_SIZE

def init_radio():
    CSN_PIN = 0  #SPI bus 0: /dev/spidev0.0
    if RF24_DRIVER == "MRAA":
        CE_PIN = 15  
    elif RF24_DRIVER == "wiringPi":
        CE_PIN = 3  
    else:
        CE_PIN = 22
    radio = RF24(CE_PIN, CSN_PIN)

    if not radio.begin(25, 0):
        raise RuntimeError("Radio hardware is not responding")

    address = [b"1Node", b"2Node"]

    radio_number = bool(
        int(input("SELECT THE OPERATION MODE:'0' for TX_TRANSMITTING or '1'  for RX_RECEIVING ") or 0)
    )

    # Enable the custom ACK payload feature
    radio.enableAckPayload()

    # Set Power Amplifier level to -12 dBm for close proximity
    radio.setPALevel(RF24_PA_LOW)  # RF24_PA_MAX is default

    # Set the TX address of the RX node into the TX pipe
    radio.openWritingPipe(address[radio_number])  # Always uses pipe 0

    # Set the RX address of the TX node into a RX pipe
    radio.openReadingPipe(1, address[not radio_number])  # Using pipe 1

    radio.payloadSize = SIZE

    radio.printPrettyDetails()
    return radio, radio_number

def build_packets(file_buff: bytes) -> List[bytes]:
    packet_buff = []
    length = len(file_buff)
    num_packets = math.ceil(length / PAYLOAD_SIZE)

    for i in range(num_packets):
        header = struct.pack('BB', i, num_packets)
        payload = file_buff[i * PAYLOAD_SIZE:PAYLOAD_SIZE * (i + 1)]
        packet_buff.append(header + payload)

    return packet_buff

def change_to_Tx(radio):
    radio.stopListening()  # Put radio in TX mode
    radio.flush_tx()  # Clear the TX FIFO so we can use all 3 levels
    return radio

def master(radio):
    radio = change_to_Tx(radio)

    # Read "Fitxer.txt" from the current directory and send it. Need to prepare the file from the USB, copy it on current directory and rename to Fitxer.txt
    file_path = "Fitxer.txt"
    if not os.path.exists(file_path):
        print(f"ERROR: {file_path} not found!")
        return

    with open(file_path, 'rb') as f:
        file_buff = f.read()

    packet_buff = build_packets(file_buff)

    i = 0
    while i < len(packet_buff):
        radio.write(packet_buff[i])
        print(f"PACKET TRANSMITTED:  {packet_buff[i]}")
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            print("ACK received")
            length = radio.getDynamicPayloadSize()
            ack = radio.read(length)
            print(f"ACK received {ack}")
            if len(ack) >= 1 and ack[0] == i:
                print(f"Packet {i} received")
                i += 1

def slave(radio):
    """Listen for any payloads and print them out (suffixed with received counter)."""
    radio.startListening()  # Put radio in RX mode
    receive_payload = b''
    next_packet = 0
    radio.writeAckPayload(1, struct.pack('B', next_packet))  # Load ACK for first response

    while True:
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            new_payload = radio.read(SIZE)  # Read the new payload
            if next_packet == new_payload[0]:
                receive_payload += new_payload[HEADER_SIZE:SIZE]
                print(f"PACKET RECEIVED: {next_packet}")
                print(f"DATA RECEIVED: {receive_payload}")
                next_packet += 1
            radio.writeAckPayload(1, struct.pack('B', new_payload[0]))

            if next_packet == new_payload[1]:
                break

    # Save the received data into a file in the current directory
    file_path = '_file_received.txt'
    with open(file_path, 'wb') as file:
        file.write(receive_payload)

    print(f"File saved as {file_path}")
    radio.stopListening()  # Put the radio in TX mode

def set_role(radio, mode) -> bool:
    if mode == 1:
        slave(radio)
        return True
    else:
        master(radio)
        return True

if __name__ == "__main__":
    radio, mode = init_radio()
    try:
        set_role(radio, mode)
        radio.powerDown()
    except KeyboardInterrupt:
        print("Keyboard Interrupt detected. Powering down radio.")
        radio.powerDown()
else:
    print("Run slave() on receiver\nRun master() on transmitter")
