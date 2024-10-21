###############################################################################
#########################   LIBRARIES IMPORT    ###############################
###############################################################################
import time
import board
import os
import digitalio as dio
from gpiozero import LED,Button
import struct
import zlib
import math
import logging
from circuitpython_nrf24l01.rf24 import RF24
from glob import glob # To search
from subprocess import check_output, CalledProcessError


###############################################################################
#########################   INIZIALIZATION BLOCK    ###########################
###############################################################################

########### LEDs AND BUTTONS INIZIALIZATION #########
led_tx = LED(22)
led_rx = LED(15)
led_state = LED(5)
button_mode = Button(17,pull_up=True,bounce_time = 0.3)
button_select = Button(27,pull_up=True,bounce_time = 0.3)
led_tx.off()
#led_rx.on()
led_state.off()

########### FLAGS INIZIALIZATION #########
select_path = False
select_file = False
create_file = False
state = 1 # 1->TX 0->RX
Mode_select = 1 #   Bypass for buttons ( 1 bypass)
bypass = True #False per TX

########### NRF24L01+ INIZIALIZATION #########
pipe_num = 0
N_packets=0
data_compressed=""
ce = dio.DigitalInOut(board.D26)
csn = dio.DigitalInOut(board.D24)
spi = board.SPI()
nrf = RF24(spi, csn, ce)
nrf.ack = False  # Enables custom ACK payload
nrf.pa_level = -6 # Power level of: 0, -6, -12, -18 dBm
nrf.data_rate = 250 #Bit rate of: 2 (Mbps), 1 (Mbps), 250 (kbps); Insert value
nrf.channel = 83 #Default channel 76 (2.476 GHz). MAX channel 83. 2.482 GHz
nrf.arc = 15 #Number of retransmits, default is 3. Int. Value: [0, 15]
nrf.ard = 1000 #Retransmission time from [250, 4000] in microseconds
nrf.auto_ack = True
nrf.crc = 2 #Default 2. Number of bytes for the CRC. Int. Value: [0, 2]
size_initial = 32 #Default value 32. Number of payload bytes, Int Value: [1, 32]
nrf.payload_length = size_initial
address = b"TEAMA" #Address to put in the Rx and Tx pipes in a buffer protocol object (bytearray)
nrf.listen = True
nrf.flush_rx()
nrf.open_rx_pipe(pipe_num,address)

########### BYPASS CONFIGURATION #########
if bypass: #If bypass=1 --> LOCAL Storage ; If bypass=0 --> USB MOUNTED Storage
    select_path = True
    select_file = True
    path = os.path.dirname(os.path.realpath(__file__))
    if state:
        file_path = path+"/in.txt" #Input file to TX in local Tests
    else:
        file_path = path+"/out.txt" #Output file to storage the Rx data in local Tests

    os.system("lxterminal -e 'echo START;read'") #Analog to start button
    now = time.monotonic() * 1000 #Startiong time of transmission saved
    #NOTE: To start the Tx or Rx execution is necessary to press enter! The lxterminal will be close and the device will be ready to Tx/Rx

###############################################################################
#########################   USB FUNCTIONS    ##################################
###############################################################################

########### GET USB #########
def get_usb_devices(): #Selects the usb device once it is mounted
    sdb_devices = map(os.path.realpath, glob('/sys/block/sd*'))
    usb_devices = (dev for dev in sdb_devices
        if 'usb' in dev.split('/')[5])
    return dict((os.path.basename(dev), dev) for dev in usb_devices)

########### GET MOUNT POINTS #########
def get_mount_points(devices=None): #Detects the mounted USB devices
    devices = devices or get_usb_devices()  # if devices are None: get_usb_devices
    output = check_output(['mount']).splitlines()
    output = [tmp.decode('UTF-8') for tmp in output]

    def is_usb(path): #Gets the usb path
        return any(dev in path for dev in devices)
    usb_info = (line for line in output if is_usb(line.split()[0]))
    return [(info.split()[2]) for info in usb_info]

###############################################################################
#########################   GENERAL FUNCTIONS    ##############################
###############################################################################

########### END COMMUNICATIONS FUNCTION #########
def end_comms(): #Ends the communication once the Tx-Rx is performed
    print("The communication has ended.")
    os.system("lxterminal -e 'echo The communication has ended;bash'") #Pop-up lxterminal with "Communication ending notification"
    #NOTE: To end the programme the lxterminal must be closed!
    exit() #Closes the programme to reduce unuseful consumption

###############################################################################
#########################   TRANSMISSION FUNCTION    ##########################
###############################################################################

def transmit(number_of_packets, data_to_send):

########### TRANSMISSION INITIALIZATION #########
    nrf.listen = False  # Put radio in TX mode (Used also for power saving)
    print("Transmission mode:")
    #Set address of RX node into a TX pipe
    nrf.open_tx_pipe(address) #TINDRIA MES SENTIT POSAR UNA ADREÇA DIFERENT A TX i RX
    i = 0 #Initialization of the counter
    send_rep = 0 #Send() attempts variable, màxim 5
    max_send_rep = 5 #Maximum number of send() attempts repetitions
    print("We have ",number_of_packets," packets to transmit.")
    print("The transmission starts. Please, wait.")
    average_time=0; #Average time taken to transmit each packet
    number_retry = 0 #Number of retry

    while i < number_of_packets:
        resend = False
        # if not i % 20: print(i) #Per veure quin número de paquet estem enviant

########### BUFFER FILLING FOR TRANSMISSION #########
        # CASE 1: LAST PACKET TO SEND. The buffer is filled with the remaining data and empty bytes
        if i == number_of_packets -1: #Last packet to send
            flag_last_packet = 1 #Set flag_last_packet bit to high (1)
            #Compute payload size of last packet
            last_bytes = size_compressed_file - i*size_final
            flag_payload_size = last_bytes #Set flag_payload_size to the size we send
            flag_packet_id = i % 4
            flags = flag_last_packet + (last_bytes<<1) + (flag_packet_id<<6)
            control_byte = bytes([flags]) #Further changes can be done to falgs
            empty_data = b'~'*(size_final - last_bytes) #Add redundant data to get 32 byte payload
            buffer = control_byte +  data_to_send[i*size_final : ] + empty_data #Join all data

        # CASE 2: NORMAL PACKET TO SEND. The buffer is completely filled with data
        else:
            flag_last_packet = 0 #Set flag_last_packet byte to 0
            flag_packet_id = i % 4
            flags = flag_last_packet + (size_final<<1) + (flag_packet_id<<6) #Payload size = size_final
            control_byte = bytes([flags]) #Payload size = 31 + flag_last_packet
            buffer = control_byte +  data_to_send[i*size_final : i*size_final+size_final]

########### DATA TRANSMISSION #########
        ###Load buffer varaible to send the payload to RX###
        #ACK_payload = nrf.send(buf, ask_no_ack=False, force_retry=0, send_only=False)
        # result =: [=True --> no ACK payload; ="Payload" --> ACK payload; =False --> no ACK received]
        if not resend:
            #RF24.send(buf, ask_no_ack=False, force_retry=0, send_only=False)
            result = nrf.send(buffer, False, 0, False)
        else:
            result = nrf.send(buffer, False, 0, False)
        observer = nrf._reg_read(8)
        number_retry = number_retry + (observer & 0x0F)

########### ACKNOWLEDGE #########
        if not result: #Podem afegir limit de intents de send()
            #print("Send() failed or timed out")
            #In case of not receiveing ACK, retransmit same packet i (NO increment)
            resend = True
            send_rep += 1 #Increment send attempts variable
        else:
            #Transmission and reception is OK.
            #print("raw ACK: {}".format(repr(result))) #Print ACK payload received
            resend = False
            i += 1 #Send next data payload
            send_rep = 0 #Reset counter of send() function repetitions
            time.sleep(1/1000000) #1 microsecond sleep time (allow Rx to prepare new ACK payload)

########### TIMING ANALYSIS #########
    end = time.monotonic() * 1000
    average_time = (end-now)/number_of_packets #Average time taken for each packet Tx
    print("Retransmissions computed with observer:", number_retry) #Number of retransmissions
    print("Average time per packet:",average_time)
    print("Transmission took:", end - now, "ms") #CAL que estigui dins e while

########### TIMING ANALYSIS REPORT GENERATION #########
    path_report_file = path+'/'+'reportTx.txt'
    MyReportFile = open(path_report_file,"w")
    MyReportFile.write("Retransmissions computed with observer:"+str(number_retry)+'\n'+"Average time per packet:"+str(average_time)+'\n'+"Transmission took:"+ str(end - now)+ "ms."+'\n')
    MyReportFile.close()

########### COMMUNICATION ENDING #########
    if flag_last_packet:
        end_comms()
        #Podem afegir un timer de tota la transmisio si voleu (ha d'anar fora del while)


###############################################################################
#########################   RECEPTION FUNCTION    ##########################
###############################################################################

def receive(): #Returns file with all data received

########### RECEPTION INITIALIZATION #########
    print("Reception mode:")
    print("The transmission starts. Please, wait.")
    #Pipe number: The data pipe to use for RX transactions. Range: [0, 5].
    #nrf.open_rx_pipe(pipe_number, address_of_RX)
    nrf.open_rx_pipe(pipe_num, address)
    nrf.listen = True    ###RX mode is set###
    #ACK_payload = b"Next" # Set ACK payload to 0 (binary payñload, 0 or 1 only)
    #Size: [1, 32] Bytes.
    #buffer_ack = ACK_payload #We will only have 2 posisble messages to be acknowladged
    ###LOAD FIRST ACK RESPONSE WITH OUR PAYLOAD###
    #Lo dels pipes es pq pot rebre de fins a 6 Tx a la "vegada"!!!!! --> Mirar exemple multiceiver_test.py
    #nrf.load_ack(buffer_ack, 0) #Select correctly the pipe number.
    file_received = b'' #Initialization of the bytes string of the received data
    flag_last_packet = 0
    flag_packet_id = 0
    i = 0
    start = time.monotonic() #Timer initialization

############# DATA PAYLOAD OBTANTION  ###########
    #Repeat until flag_last_packet = 1 or timer ends
    while not flag_last_packet:
        if nrf.any(): #Checks if data has been received, returns 0 if no data.
            #Print received packet payload length in bytes
            #print("Found {} bytes on pipe {}".format(nrf.any(), nrf.pipe))
            if not nrf.irq_df:
                rx = nrf.recv() #Clears flags & empties RX FIFO, saves bytes in rx
                control_byte_integer = int.from_bytes(rx[0 : 1], "big") #Pass to int value the control byte
                flag_last_packet = control_byte_integer & (0x01) #Emmascarat per 0000001
                flag_payload_size = (control_byte_integer & (0x3E))>>1 #Emmascarat per 00111110
                flag_packet_id = (control_byte_integer & (0xC0))>>6 #Emmascarat per 00111110
                payload_size = flag_payload_size + 1
                if i == flag_packet_id: #Here, we look if the packet is not repeated
                    file_received = file_received + rx[1 : payload_size] #Data concatenation
                    i = (i + 1) % 4 #We always use 2 bits for this flag (flag_packet_id)

############# PAYLOAD ACK  ###########
                    #if not flag_last_packet:  #Case of flag_last_packet = 0 (not last packet)
                        #ACK_payload = (ACK_payload + 1) % 1 #Increase ACK payload value (between 0 and 1)
                    #    ACK_payload = b"Next"
                    #    buffer_ack = ACK_payload #pass int to byte
                    #    nrf.load_ack(buffer_ack, 0) # load ACK for next response
                    #else:
                        # load ACK for next response, ACK with EOF payload for receiver
                    #    nrf.load_ack(b"EOF", 0)

############# RECEIVED DATA SAVED  ###########
    file_decompressed = zlib.decompress(file_received) #Decompression
    MyFile = open(file_path,"wb")
    MyFile.write(file_decompressed)
    MyFile.close()

############# TIMING ANALYSIS REPORT GENERATION  ###########
    end=time.monotonic() * 1000
    print("Reception took:", end - now, "ms") #CAL que estigui dins e while
    path_report_file = path+'/'+'reportRx.txt'
    MyReportFile = open(path_report_file,"w")
    MyReportFile.write("Reception took:"+str(end-now)+"ms")
    MyReportFile.close()

############# END COMMUNICATION  ###########
    nrf.listen = False  #Put receiver in idle mode (Tx)
    nrf.flush_tx()  #Flush any remaining ACK payload
    end_comms()


###############################################################################
#########################   MAIN FUNCTION    ##################################
###############################################################################

while True:

############# BYPASS FOR LOCAL OR USB MOUNTED DEVICE  ###########
    if not select_path and len(get_mount_points()) != 0: #If bypass=1 --> path is local; if bypass=0 --> path is USB mounted device
        path=get_mount_points()[0]
        select_path=True

############# BYPASS FOR MANUAL (SOFTWARE) OR BUTTONS (HARDWARE) MODE SELECTION  ###########
    if not Mode_select: #If Mode_select=1 --> Software setup; If Mode_select=0 --> Hardware/buttons setup

        if button_mode.is_pressed:

            if state:
                led_tx.off()
                #led_rx.on()
                state = 0
            else:
                led_tx.on()
                #led_rx.off()
                state = 1

        if button_select.is_pressed:
            led_state.on()  # no(només si tenim 3 leds)
            Mode_select = 1
            now = time.monotonic() * 1000 #Startiong time of transmission saved
    else:

############# TRANSMISSION PROCESS  ###########
        if state and select_path:
            if not select_file:
                for files in os.listdir(path):
                    if os.path.isfile(os.path.join(path, files)) and files.endswith('.txt'):
                        file_path=path+'/'+files
                        select_file=True
                        print(file_path)
            else:
                with open(file_path, 'rb') as f:
                    contents = f.read()
                data_compressed = zlib.compress(contents,-1)
                size_compressed_file = len(data_compressed)
                size_final = size_initial - 1
                N_packets = math.ceil(size_compressed_file/size_final)
                transmit(N_packets,data_compressed)

############# RECEPTION PROCESS  ###########
        elif not state and select_path:
            if not create_file:
                myFile = open(path+'/'+'out.txt', "w+")
                RX_ready = True
                create_file =True
            else:
                receive()
