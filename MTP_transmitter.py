import os
import spidev
import RPi.GPIO as GPIO
import nrf24
import time
import zlib

# Inicialitzem la configuració del mòdul nRF24L01
radio = nrf24.NRF24(GPIO, spidev.SpiDev())  # Aquí es crea l'objecte "radio"
radio.begin(0, 17)  # Configurem els pins de la Raspberry Pi

radio.setPALevel(nrf24.PA_MAX)  # Altres opcions: PA_MIN, PA_HIGH, PA_LOW
radio.setDataRate(nrf24.BR_250KBPS)  # Altres opcions: BR_1MBPS, BR_2MBPS
radio.setChannel(76)  # Canal
radio.setCRCLength(nrf24.NRF24_CRC_16)  # CRC de 16 bits
radio.setRetries(2, 15)  # Retràs de 2 * 250 µs, fins a 15 reintents
radio.setPayloadSize(32)  # Configura la mida del payload
radio.setAutoAck(True)  # Activar l'ACK automàtic
radio.enableDynamicPayloads()  # Habilita càrrega útil dinàmica
radio.enableAckPayload()  # Habilita càrrega útil a l'ACK
radio.openWritingPipe(b'1Node')  # Direcció del transmissor
radio.openReadingPipe(1, b'2Node')  # Direcció del receptor
radio.stopListening()  # Mòdul en mode de transmissió

def obtenir_primer_txt(ruta_usb):
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
    
def llegir_fitxer_per_blocs(ruta_arxiu, mida_bloc):
    try:
        with open(ruta_arxiu, 'r') as arxiu:
            while True:
                bloc = arxiu.read(mida_bloc)
                if not bloc:
                    break  # Final de l'arxiu
                yield bloc  # Retorna cada bloc (yield per usar-lo com a generador)
    except FileNotFoundError:
        print(f"Arxiu no trobat: {ruta_arxiu}")
        return None
    
def comprimir_dades_per_bloc(bloc):
    # Comprimir el bloc
    bloc_comprimit = zlib.compress(bloc.encode('utf-8'))
    return bloc_comprimit

def dividir_en_fragments(contingut, mida_fragment=32):
    fragments = [contingut[i:i + mida_fragment] for i in range(0, len(contingut), mida_fragment)]
    return fragments

def enviar_bloc(bloc):
    # Dividir el bloc comprimit en fragments de 32 bytes
    fragments = dividir_en_fragments(bloc)

    for fragment in fragments:
        # Ajustar la mida del fragment a la mida de la payload
        if len(fragment) < 32:
            fragment += bytes(32 - len(fragment))  # Omplir amb zeros si es menor de 32 bytes
        
        # Enviar el fragment
        resultado = radio.write(fragment)
        if resultado:
            print(f"Fragment enviat: {fragment}")
        else:
            print(f"Error a l'enviar el fragment: {fragment}")

    # Enviar el fragment de final de bloc
    final_bloc = bytes(32)  # Fragment ple de zeros per indicar el final de bloc
    radio.write(final_bloc)  # Enviar el fragment de final de bloc
    print("Fragment de final de bloc enviat.")

    # Enviar el fragment de final de document
    final_document = bytes(32)  # Fragment ple de zeros per indicar el final de document
    radio.write(final_document)  # Enviar el fragment de final de document
    print("Fragment de final de document enviat.")

# Funció per gestionar la recepció de peticions de reenvio
def gestionar_peticio_reenvio():
    radio.startListening()  # Canviar a mode receptor
    while True:
        if radio.available(0):
            rebut = []
            radio.read(rebut, radio.getDynamicPayloadSize())
            peticio = bytes(rebut)
            if peticio == b'REENVIAR':
                # Aquí podries gestionar quina part del bloc es demana tornar a enviar
                print("Petició de reenvio rebuda.")
                return True

ruta_usb = '/media/pi/USB_DISK/'  # Cambiar si el dispositiu té una altra ruta
ruta_arxiu_txt = obtenir_primer_txt(ruta_usb)

if ruta_arxiu_txt:
    # Llegir l'arxiu per blocs (per exemple, 1 KB per bloc)
    mida_bloc = 1024  # Llegir d'1 KB en 1 KB

    for bloc in llegir_fitxer_per_blocs(ruta_arxiu_txt, mida_bloc):
        # Comprimir cada bloc de l'arxiu abans d'enviar-lo
        bloc_comprimit = comprimir_dades_per_bloc(bloc)

        # Enviar el bloc comprimit
        enviar_bloc(bloc_comprimit)

        # Esperar a gestionar qualsevol petició de reenvio
        if gestionar_peticio_reenvio():
            enviar_bloc(bloc_comprimit)  # Reenviar el bloc si es demana

else:
    print("No s'ha trobat cap arxiu .txt al dispositiu USB.")

GPIO.cleanup()  # Netejar els pins GPIO després d'utilitzar