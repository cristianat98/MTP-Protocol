import time
import board
from digitalio import DigitalInOut
from circuitpython_nrf24l01.rf24 import RF24
import os
import zlib

SPI_BUS, CSN_PIN, CE_PIN = (None, None, None)

try:  # on Linux
    import spidev

    SPI_BUS = spidev.SpiDev()  # for a faster interface on linux
    CSN_PIN = 0  # use CE0 on default bus (even faster than using any pin)
    CE_PIN = DigitalInOut(board.D22)  # using pin gpio22 (BCM numbering)

except ImportError:  # on CircuitPython only
    SPI_BUS = board.SPI()  # init spi bus object

    CE_PIN = DigitalInOut(board.D8)
    CSN_PIN = DigitalInOut(board.D22)

nrf = RF24(SPI_BUS, CSN_PIN, CE_PIN)

nrf.pa_level = -18
nrf.auto_ack = True
nrf.ack = False  # Enables custom ACK payload
nrf.pa_level = 0 # Power level of: 0, -6, -12, -18 dBm
nrf.data_rate = 2 #Bit rate of: 2 (Mbps), 1 (Mbps), 250 (kbps); Insert value
nrf.channel = 83 #Default channel 76 (2.476 GHz). MAX channel 83. 2.482 GHz
nrf.arc = 15 #Number of retransmits, default is 3. Int. Value: [0, 15]
nrf.ard = 2000 #Retransmission time from [250, 4000] in microseconds
nrf.auto_ack = True
#nrf.payload_length = 32
nrf.crc = 2 #Default 2. Number of bytes for the CRC. Int. Value: [0, 2]

# set TX address of RX node into the TX pipe
nrf.open_tx_pipe(b"AAA")  # always uses pipe 0
# set RX address of TX node into an RX pipe
nrf.open_rx_pipe(0, b"AAA")  # using pipe 1

empty = b'1'*32

######### TRANSMITTER FUNCTIONS

def get_data_file():
    # TODO: Determine USB path
    ruta_usb = '/media/pi/USB_DISK/'
    ruta_arxiu_txt = find_file(ruta_usb)

    if not ruta_arxiu_txt:
        print("No s'ha trobat cap arxiu .txt al dispositiu USB.")
        return False

    try:
        with open(ruta_arxiu_txt, 'r') as arxiu:
            return arxiu.read()
    except FileNotFoundError:
        print(f"Arxiu no trobat: {ruta_arxiu_txt}")
        return None


def find_file(ruta_usb):
    try:
        # Llistar arxius en el directorio de la ruta USB
        arxius = os.listdir(ruta_usb)

        # Filtrar arxius .txt i retornar el primer
        for arxiu in arxius:
            if arxiu.endswith('.txt'):
                ruta_arxiu = os.path.join(ruta_usb, arxiu)
                print(f"Arxiu trobat: {ruta_arxiu}")
                return ruta_arxiu
        print("No s'ha trobat cap arxiu .txt a l'USB.")
        return None
    except FileNotFoundError:
        print(f"No es troba el directori {ruta_usb}")
        return None


def dividir_en_fragments(contingut, mida_fragment=32):
    fragments = [
        contingut[i:i + mida_fragment] for i in range(
            0, len(contingut), mida_fragment
        )
    ]
    return fragments


def enviar_bloc(bloc, nrf):
    # Dividir el bloc comprimit en fragments de 32 bytes
    fragments = dividir_en_fragments(bloc)

    for fragment in fragments:
        # Ajustar la mida del fragment a la mida de la payload
        if len(fragment) < 32:
            fragment += bytes(32 - len(fragment))  # Omplir amb zeros si es menor de 32 bytes

        # Enviar el fragment
        resultado = nrf.send(fragment, True, 15, False)
        if resultado:
            print(f"Fragment enviat: {fragment}")
        else:
            print(f"Error a l'enviar el fragment: {fragment}")

    # Enviar el fragment de final de bloc
    final_bloc = bytes(32)  # Fragment ple de zeros per indicar el final de bloc
    nrf.send(final_bloc, True, 15, False)  # Enviar el fragment de final de bloc
    print("Fragment de final de bloc enviat.")


# Funció per gestionar la recepció de peticions de reenvio
def gestionar_peticio_reenvio(rnf):
    nrf.startListening()  # Canviar a mode receptor
    while True:
        if nrf.any():
            rebut = nrf.read(nrf.any())
            peticio = bytes(rebut)
            if peticio == b'REENVIAR':
                # Aquí podries gestionar quina part del bloc es demana tornar a enviar
                print("Petició de reenvio rebuda.")
                return True

def transmitter(nrf):
    nrf.listen = False
    data = get_data_file()
    data.encode("utf-8")

    # TODO: Blocks with full lines or split block in the middle of the line
    # Llegir l'arxiu per blocs (per exemple, 1 KB per bloc)
    mida_bloc = 1024
    blocks = [
        data[i:i + mida_bloc] for i in range(
            0, len(data), mida_bloc
        )
    ]

    for bloc in blocks:
        # Comprimir cada bloc de l'arxiu abans d'enviar-lo
        bloc_comprimit = zlib.compress(bloc.encode('utf-8'))

        # Enviar el bloc comprimit
        enviar_bloc(bloc_comprimit, nrf)

        # Esperar a gestionar qualsevol petició de reenvio
        if gestionar_peticio_reenvio(nrf):
            enviar_bloc(bloc_comprimit, bloc)  # Reenviar el bloc si es demana

    # TODO: Is this needed 
    # Enviar el fragment de final de document
    final_document = bytes(32)  # Fragment ple de zeros per indicar el final de document
    nrf.send(final_document, True, 15, False)  # Enviar el fragment de final de document
    print("Fragment de final de document enviat.")

######### RECEIVER FUNCTIONS

# Rebre els blocs comprimits en paquets de 32 bytes
def rebre_blocs(nrf, blocs_comprimits):
    bloc_actual = b''  # Bloc comprimit que s'està rebent
    while True:
        while not nrf.any():
            time.sleep(1/2000)  # Esperar

        # Llegir la payload del paquet rebut
        rebut = nrf.read(nrf.any())
        fragment = bytes(rebut)  # Convertir la llista d'enters a bytes

        # Verificar si hem rebut l'últim paquet (un bloc ple de zeros indica el final d'un fragment)
        if set(fragment) == {0}:
            # El fragment actual ha acabat de rebre's
            blocs_comprimits.append(bloc_actual)
            bloc_actual = b''  # Reiniciar pel proper bloc
            print("Fragment rebut i guardat.")

            # Verificar si aquest paquet especial és l'últim de tots els fragments (fi de transmissió)
            if len(blocs_comprimits) > 0 and set(blocs_comprimits[-1]) == {0}:
                print("Tots els fragments han estat rebuts.")
                blocs_comprimits.pop()  # Remoure el paquet buit final
                break
            continue

        # Acumular el fragment al bloc actual
        bloc_actual += fragment


# Funció per descomprimir cada bloc al moment de rebre'l
def descomprimir_blocs(bloc, blocs_descomprimits):
    try:
        bloc_descomprimit = zlib.decompress(bloc)
        blocs_descomprimits.append(bloc_descomprimit)  # Guardar les dades descomprimides
        print("Bloc descomprès amb èxit.")
        return True  # Indicar que la descompressió va tenir èxit
    except zlib.error as e:
        print(f"Error al descomprimir el bloc: {e}")
        return False  # Indicar que la descompressió ha fallat


# Funció per enviar una petició de reenvio
def enviar_peticio_reenvio(nrf):
    nrf.listen = False
    peticio = b'REENVIAR'  # Contingut de la petició
    nrf.send(peticio, True, 15, False)  # Enviar la petició
    nrf.listen = True  # Tornar a mode receptor
    print("Petició de reenvio enviada.")


# Funció per guardar les dades descomprimides en un arxiu txt
def guardar_a_arxiu(dades, ruta_arxiu):
    with open(ruta_arxiu, 'wb') as arxiu:
        arxiu.send(dades, True, 15, False)  # Guardar les dades com a bytes
    print(f"Arxiu guardat correctament a: {ruta_arxiu}")


# Funció principal del receptor
def receiver(nrf):
    # Guardar els blocs rebuts
    blocs_comprimits = []
    blocs_descomprimits = []  # Guardar les dades descomprimides
    print("Esperant blocs...")

    # Rebre tots els blocs comprimits
    rebre_blocs(nrf, blocs_comprimits)

    # Descomprimir els fragments i gestionar possibles errors
    for bloc in blocs_comprimits:
        if not descomprimir_blocs(bloc, blocs_descomprimits):
            # Si la descompressió falla, enviar una petició per reenviar el bloc
            enviar_peticio_reenvio(nrf)

    # TODO: Determine USB location
    # Guardar les dades descomprimides en un arxiu txt
    ruta_arxiu_guardat = '/media/pi/USB_DISK/received_file.txt'  # Ruta on guardar el fitxer al USB
    guardar_a_arxiu(b''.join(blocs_descomprimits), ruta_arxiu_guardat)  # Guardar les dades descomprimides

mode = input("El mòdul serà transmissor o receptor? (T/R): ").strip().upper()

if mode == 'T':
    transmitter(nrf)

elif mode == 'R':
    receiver(nrf)

else:
    print("Opció no vàlida. Si us plau, escull 'T' per transmissor o 'R' per receptor.")
