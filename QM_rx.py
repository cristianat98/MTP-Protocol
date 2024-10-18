# MTP
import time
import struct
import board
from digitalio import DigitalInOut


# if running this on a ATSAMD21 M0 based board
# from circuitpython_nrf24l01.rf24_lite import RF24
from circuitpython_nrf24l01.rf24 import RF24


SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)
try:
    import spidev
    SPI_BUS = spidev.SpiDev()
    CSN_PIN = 0
    CE_PIN = DigitalInOut(board.D22)
except ImportError:
    SPI_BUS = board.SPI()
    CE_PIN = DigitalInOut(board.D4)
    CSN_PIN = DigitalInOut(board.D5)


nrf = RF24(SPI_BUS, CSN_PIN, CE_PIN)


nrf.pa_level = -18
nrf.auto_ack = True
nrf.ack = False  # Enables custom ACK payload
nrf.pa_level = -18 # Power level of: 0, -6, -12, -18 dBm
nrf.data_rate = 2 #Bit rate of: 2 (Mbps), 1 (Mbps), 250 (kbps); Insert value
nrf.channel = 83 #Default channel 76 (2.476 GHz). MAX channel 83. 2.482 GHz
nrf.arc = 15 #Number of retransmits, default is 3. Int. Value: [0, 15]
nrf.ard = 2000 #Retransmission time from [250, 4000] in microseconds
nrf.auto_ack = True
#nrf.payload_length = 32
nrf.crc = 2 #Default 2. Number of bytes for the CRC. Int. Value: [0, 2]
#nrf.flush_rx()
#nrf.flush_tx()

# set TX address of RX node into the TX pipe
nrf.open_tx_pipe(b"AAA")  # always uses pipe 0

# set RX address of TX node into an RX pipe
nrf.open_rx_pipe(0, b"AAA")  # using pipe 1


payload = [0.0]


rx_bit_flip = 0


def slave(timeout=5):
    global rx_bit_flip
    nrf.listen = True
    received_data = bytearray()
    start = time.monotonic()
    while (time.monotonic() - start) < timeout:
        if nrf.available():
            while nrf.available():
                buffer = nrf.read(nrf.any())
                received_bit_flip = buffer[0]
                if received_bit_flip == rx_bit_flip:
                    print("Received chunk: {}...".format(buffer[:10]))
                    received_data += buffer[1:]  
                    rx_bit_flip ^= 1
                else :
                    print("Out of sequence packet")
            start = time.monotonic()
    nrf.listen = False
    valid_data_end = len(received_data.rstrip(b'\x00'))
    valid_data = received_data[:valid_data_end]
    with open("received_file.txt", "wb") as file:
        file.write(valid_data)
        print(f"Archivo reconstruido y guardado. Tamaño total: {len(received_data)} bytes.")




print("Running RX")
try:
    slave()
except KeyboardInterrupt:
    print(" Keyboard Interrupt detected. Powering down radio...")
    nrf.power = False
