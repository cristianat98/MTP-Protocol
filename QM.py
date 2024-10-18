import time
import struct
import board
from digitalio import DigitalInOut
from circuitpython_nrf24l01.rf24 import RF24

SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)

try:  # on Linux
    import spidev

    SPI_BUS = spidev.SpiDev()  # for a faster interface on linux
    CSN_PIN = 0  # use CE0 on default bus (even faster than using any pin)
    CE_PIN = DigitalInOut(board.D22)  # using pin gpio22 (BCM numbering)

except ImportError:  # on CircuitPython only
    SPI_BUS = board.SPI()  # init spi bus object

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




# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
#payload = [0.0]
empty = b'1'*32

# uncomment the following 3 lines for compatibility with TMRh20 library
# nrf.allow_ask_no_ack = False
# nrf.dynamic_payloads = False
# nrf.payload_length = 4

def master(count=200):  # count = 5 will only transmit 5 packets
    """Transmits an incrementing integer every second"""
    nrf.listen = False  # ensures the nRF24L01 is in TX mode
    total = count
    start_total_time = time.monotonic_ns()
    nsuccess = 0
    count=0
    ttime = 0
    transmitted_bytes=0
    while transmitted_bytes<50000:
        # use struct.pack to structure your data
        # into a usable payload
        #buffer = struct.pack("<f", payload[0])
        buffer = empty
        size = len(buffer)
        # "<f" means a single little endian (4 byte) float value.
        start_timer = time.monotonic_ns()  # start timer
        result = nrf.send(buffer, False, 0, False)
        end_timer = time.monotonic_ns()  # end timer
        rest = end_timer - start_timer
        #print(result)
        if not result:
            #print("err")
            a=0
        else:
            nsuccess += 1
            transmitted_bytes += size
            #print("percentage :", transmitted_bytes/500000, "%")
            #payload[0] += 1
        #time.sleep(0.1)
        count += 1
    final_total_time = time.monotonic_ns()
    print(size)
    print("succes rate", nsuccess/count, "%")
    print("total bytes transmitted", nsuccess*size)
    print("total time", (final_total_time-start_total_time))
    print(" bitrate" + str(nsuccess*size*8/((final_total_time-start_total_time)/1e+9)))

tx_bit_flip = 0

def send_chunk(buffer):
    global tx_bit_flip
    first_byte = tx_bit_flip
    buffer = bytes([first_byte]) + buffer
    while not nrf.send(buffer):
        print("ERROR")
    tx_bit_flip ^= 1

def send_file():
    file_path = "transmittedFile.txt"
    with open(file_path, "rb") as file:
        file_content = file.read()
    nrf.listen = False  
    chunk_size = 31 
    total_chunks = len(file_content) // (chunk_size) + (1 if len(file_content) % (chunk_size) else 0)
    for i in range(total_chunks):
        start = i * (chunk_size)
        end = start + (chunk_size)
        chunk = file_content[start:end]
        #if len(chunk) < chunk_size:
         #   chunk += b'\x00' * (chunk_size - len(chunk))
        send_chunk(chunk)
        print((i+1)/total_chunks, " %")

print("Running RX")
try:
    send_file()
except KeyboardInterrupt:
    print(" Keyboard Interrupt detected. Powering down radio...")
    nrf.power = False
