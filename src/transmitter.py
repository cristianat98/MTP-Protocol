import os
import zlib


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


def enviar_bloc(bloc, radio):
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


# Funció per gestionar la recepció de peticions de reenvio
def gestionar_peticio_reenvio(radio):
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


def transmitter(radio):
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
        enviar_bloc(bloc_comprimit, radio)

        # Esperar a gestionar qualsevol petició de reenvio
        if gestionar_peticio_reenvio(radio):
            enviar_bloc(bloc_comprimit, bloc)  # Reenviar el bloc si es demana

    # TODO: Is this needed 
    # Enviar el fragment de final de document
    final_document = bytes(32)  # Fragment ple de zeros per indicar el final de document
    radio.write(final_document)  # Enviar el fragment de final de document
    print("Fragment de final de document enviat.")
