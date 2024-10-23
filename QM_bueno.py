import time
import math
from RF24 import RF24, RF24_PA_LOW, RF24_DRIVER
from read_USB import *
import struct
from typing import List

SIZE = 32  # this is the default maximum payload size
HEADER_SIZE = 2
PAYLOAD_SIZE = SIZE - HEADER_SIZE

def init_radio():
    CSN_PIN = 0  # GPIO8 aka CE0 on SPI bus 0: /dev/spidev0.0
    if RF24_DRIVER == "MRAA":
        CE_PIN = 15  # for GPIO22
    elif RF24_DRIVER == "wiringPi":
        CE_PIN = 3  # for GPIO22
    else:
        CE_PIN = 22
    radio = RF24(CE_PIN, CSN_PIN)

    # initialize the nRF24L01 on the spi bus
    if not radio.begin():
        raise RuntimeError("radio hardware is not responding")

    address = [b"1Node", b"2Node"]

    radio_number = bool(
        int(input("Which mode? Enter Tx '0' or Rx '1' -> ") or 0)
    )

    # to enable the custom ACK payload feature
    radio.enableAckPayload()

    # set the Power Amplifier level to -12 dBm since this test example is
    # usually run with nRF24L01 transceivers in close proximity of each other
    radio.setPALevel(RF24_PA_LOW)  # RF24_PA_MAX is default

    # set the TX address of the RX node into the TX pipe
    radio.openWritingPipe(address[radio_number])  # always uses pipe 0
    
    # set the RX address of the TX node into a RX pipe
    radio.openReadingPipe(1, address[not radio_number])  # using pipe 1

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
    radio.stopListening()  # put radio in TX mode
    radio.flush_tx()  # clear the TX FIFO so we can use all 3 levels
    return radio

def master(radio):
    radio = change_to_Tx(radio)

    file_buff = read_file()
    packet_buff = build_packets(file_buff)

    i = 0
    while i < len(packet_buff):
        radio.write(packet_buff[i])
        print(f"Transmited {packet_buff[i]}")
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            # retrieve the received packet's payload
            print("ACK received")
            length = radio.getDynamicPayloadSize()
            ack = radio.read(length)
            print(f"ACK received {ack}")
            if len(ack) >= 1 and ack[0] == i:
                print(f"Packet {i} received")
                i+=1          

def slave(radio):
    """Listen for any payloads and print them out (suffixed with received
    counter)

    :param int timeout: The number of seconds to wait (with no transmission)
        until exiting function.
    """
    radio.startListening()  # put radio in RX mode
    receive_payload = b''
    next_packet = 0
    radio.writeAckPayload(1, struct.pack('B', next_packet))  # load ACK for first response

    while True:
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            new_payload = radio.read(SIZE)  # Read the new payload
            if next_packet == new_payload[0]:
                receive_payload += new_payload[HEADER_SIZE:SIZE]
                print(f"Packet received {next_packet}")
                print(f"Packet received {receive_payload}")
                next_packet += 1
            radio.writeAckPayload(1, struct.pack('B', new_payload[0])) 

            if next_packet == new_payload[1]:
                break

    file_path = '_file.txt'
    with open(file_path, 'xb') as file:
        # Write the bytes to the file
        file.write(receive_payload)
    path = save_file_USB('_file.txt')
    print_file_content(path)
    os.remove(file_path)
    # recommended behavior is to keep in TX mode while idle
    radio.stopListening()  # put the radio in TX mode


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
        print(" Keyboard Interrupt detected. Powering down radio.")
        radio.powerDown()
else:
    print("    Run slave() on receiver\n    Run master() on transmitter")

  
