import time
import zlib


# Rebre els blocs comprimits en paquets de 32 bytes
def rebre_blocs(radio, blocs_comprimits):
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
def enviar_peticio_reenvio(radio):
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
def receiver(radio):
    # Guardar els blocs rebuts
    blocs_comprimits = []
    blocs_descomprimits = []  # Guardar les dades descomprimides
    print("Esperant blocs...")

    # Rebre tots els blocs comprimits
    rebre_blocs(radio, blocs_comprimits)

    # Descomprimir els fragments i gestionar possibles errors
    for bloc in blocs_comprimits:
        if not descomprimir_blocs(bloc, blocs_descomprimits):
            # Si la descompressió falla, enviar una petició per reenviar el bloc
            enviar_peticio_reenvio(radio)

    # TODO: Determine USB location
    # Guardar les dades descomprimides en un arxiu txt
    ruta_arxiu_guardat = '/media/pi/USB_DISK/received_file.txt'  # Ruta on guardar el fitxer al USB
    guardar_a_arxiu(b''.join(blocs_descomprimits), ruta_arxiu_guardat)  # Guardar les dades descomprimides
