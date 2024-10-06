import spidev
import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
import time
import zlib

# Inicialitzem la configuració del mòdul nRF24L01
radio = NRF24(GPIO, spidev.SpiDev())  # Aquí es crea l'objecte "radio"
radio.begin(0, 17)  # Configurem els pins de la Raspberry Pi

radio.setPALevel(NRF24.PA_MAX)  # Altres opcions: PA_MIN, PA_HIGH, PA_LOW
radio.setDataRate(NRF24.BR_250KBPS)  # Altres opcions: BR_1MBPS, BR_2MBPS
radio.setChannel(76)  # Canal
radio.setCRCLength(NRF24.NRF24_CRC_16)  # CRC de 16 bits
radio.setRetries(2, 15)  # Retràs de 2 * 250 µs, fins a 15 reintents
radio.setPayloadSize(32)  # Configura la mida del payload
radio.setAutoAck(True)  # Activar l'ACK automàtic
radio.enableDynamicPayloads()  # Habilita càrrega útil dinàmica
radio.enableAckPayload()  # Habilita càrrega útil a l'ACK
radio.openWritingPipe(b'1Node')  # Direcció del transmissor
radio.openReadingPipe(1, b'2Node')  # Direcció del receptor
radio.startListening()  # Posa el mòdul en mode receptor

# Guardar els blocs rebuts
blocs_comprimits = []
blocs_descomprimits = []  # Guardar les dades descomprimides

# Rebre els blocs comprimits en paquets de 32 bytes
def rebre_blocs():
    bloc_actual = b''  # Bloc comprimit que s'està rebent
    while True:
        while not radio.available(0):
            time.sleep(1/2000)  # Esperar
        
        # Llegir la payload del paquet rebut
        rebut = []
        radio.read(rebut, radio.getDynamicPayloadSize())
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
def descomprimir_blocs(bloc):
    try:
        bloc_descomprimit = zlib.decompress(bloc)
        blocs_descomprimits.append(bloc_descomprimit)  # Guardar les dades descomprimides
        print("Bloc descomprès amb èxit.")
        return True  # Indicar que la descompressió va tenir èxit
    except zlib.error as e:
        print(f"Error al descomprimir el bloc: {e}")
        return False  # Indicar que la descompressió ha fallat

# Funció per enviar una petició de reenvio
def enviar_peticio_reenvio():
    radio.stopListening()  # Canviar a mode emissor
    peticio = b'REENVIAR'  # Contingut de la petició
    radio.write(peticio)  # Enviar la petició
    radio.startListening()  # Tornar a mode receptor
    print("Petició de reenvio enviada.")

# Funció per guardar les dades descomprimides en un arxiu txt
def guardar_a_arxiu(dades, ruta_arxiu):
    with open(ruta_arxiu, 'wb') as arxiu:
        arxiu.write(dades)  # Guardar les dades com a bytes
    print(f"Arxiu guardat correctament a: {ruta_arxiu}")

# Funció principal del receptor
def receptor_nrf24():
    print("Esperant blocs...")
    
    # Rebre tots els blocs comprimits
    rebre_blocs()
    
    # Descomprimir els fragments i gestionar possibles errors
    for bloc in blocs_comprimits:
        if not descomprimir_blocs(bloc):
            # Si la descompressió falla, enviar una petició per reenviar el bloc
            enviar_peticio_reenvio()
            continue  # Si hi ha error, continuar amb el següent bloc

    # Guardar les dades descomprimides en un arxiu txt
    ruta_arxiu_guardat = '/media/pi/USB_DISK/received_file.txt'  # Ruta on guardar el fitxer al USB
    guardar_a_arxiu(b''.join(blocs_descomprimits), ruta_arxiu_guardat)  # Guardar les dades descomprimides

# Executar el receptor
try:
    receptor_nrf24()
finally:
    GPIO.cleanup()  # Netejar els pins GPIO després d'utilitzar