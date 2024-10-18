import time
import digitalio
from circuitpython_nrf24l01.rf24 import RF24
import board

# Configuració del mòdul NRF24
ce_pin = board.D17  # Pin CE (GPIO 17)
csn_pin = board.D8   # Pin CSN (GPIO 8)

# Inicialització dels pins
ce = digitalio.DigitalInOut(ce_pin)
csn = digitalio.DigitalInOut(csn_pin)

# Crear l'objecte RF24
radio = RF24(ce, csn)

# Inicialitzar el mòdul
radio.begin()  # Inicialització del mòdul
radio.set_rf_channel(76)  # Canal de transmissió
radio.set_pa_level(RF24.PA_MAX)  # Potència màxima
radio.set_data_rate(RF24.BR_250KBPS)  # Velocitat de transmissió
radio.set_crc_length(RF24.CRC_16)  # CRC de 16 bits
radio.enable_dynamic_payloads()  # Habilita càrrega útil dinàmica
radio.open_writing_pipe(b'1Node')  # Pipe del transmissor
radio.open_reading_pipe(1, b'2Node')  # Pipe del receptor

# Pregunta si el mòdul serà transmissor o receptor
mode = input("El mòdul serà transmissor o receptor? (T/R): ").strip().upper()

if mode == 'T':
    # Si és transmissor
    radio.stop_listening()  # Atura l'escolta per poder transmetre
    while True:
        missatge = input("Escriu un missatge per enviar: ")
        # Converteix el missatge en bytes
        missatge_bytes = missatge.encode('utf-8')

        # Omple amb zeros per arribar a 32 bytes si cal
        missatge_bytes = missatge_bytes.ljust(32, b'\0')  
        
        # Envia el missatge
        resultat = radio.write(missatge_bytes)
        
        if resultat:
            print("Missatge enviat amb èxit!")
        else:
            print("Error enviant el missatge.")
        
        # Espera una mica abans del següent enviament
        time.sleep(1)

elif mode == 'R':
    # Si és receptor
    radio.start_listening()  # Posa el mòdul en mode escolta
    
    print("Esperant missatge...")
    
    while True:
        try:
            # Comprova si hi ha dades disponibles per rebre
            if radio.available():
                missatge_recibut = bytearray(32)  # Crear un array de bytes per rebre el missatge
                radio.read(missatge_recibut, len(missatge_recibut))  # Llegeix el missatge
                
                # Converteix la llista de bytes a una cadena
                missatge_text = missatge_recibut.decode('utf-8').rstrip('\0')  # Elimina el padding de zeros
                
                print(f"Missatge rebut: {missatge_text}")
        
        except Exception as e:
            print(f"Error rebent el missatge: {e}")
        
        time.sleep(0.5)  # Evita ocupar massa CPU

else:
    print("Opció no vàlida. Si us plau, escull 'T' per transmissor o 'R' per receptor.")


