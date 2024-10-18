

# Configuració de GPIO
GPIO.setmode(GPIO.BCM)  # Utilitza la numeració BCM dels pins de la Raspberry Pi

# Configuració del mòdul NRF24
ce_pin = 22  # Pin CE
csn_pin = 8  # Pin CSN (GPIO 8 = CE0 per SPI)

radio = NRF24(GPIO, ce_pin, csn_pin)
radio.begin(0, csn_pin)  # Configurem els pins CE i CSN

# Configuració de paràmetres del mòdul
radio.setPALevel(NRF24.PA_MAX)  # Potència màxima
radio.setDataRate(NRF24.BR_250KBPS)  # Velocitat de transmissió
radio.setChannel(76)  # Canal de transmissió
radio.setCRCLength(NRF24.CRC_16)  # CRC de 16 bits
radio.setRetries(2, 15)  # Retràs de 2 * 250 µs, fins a 15 reintents
radio.setPayloadSize(32)  # Configura la mida del payload
radio.setAutoAck(True)  # Activar l'ACK automàtic
radio.enableDynamicPayloads()  # Habilita càrrega útil dinàmica
radio.enableAckPayload()  # Habilita càrrega útil a l'ACK

# Pipes de comunicació
transmitter_pipe = b'1Node'
receiver_pipe = b'2Node'
radio.openWritingPipe(transmitter_pipe)  # Pipe del transmissor
radio.openReadingPipe(1, receiver_pipe)  # Pipe del receptor

# Pregunta si el mòdul serà transmissor o receptor
mode = input("El mòdul serà transmissor o receptor? (T/R): ").strip().upper()

if mode == 'T':
    # Si és transmissor
    radio.stopListening()  # Atura l'escolta per poder transmetre
    while True:
        missatge = input("Escriu un missatge per enviar: ")
        # Converteix el missatge en una llista de bytes
        missatge_bytes = list(missatge.encode('utf-8'))
        # Omple amb zeros per arribar a 32 bytes si cal
        while len(missatge_bytes) < 32:
            missatge_bytes.append(0)
        
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
    radio.startListening()  # Posa el mòdul en mode escolta
    
    print("Esperant missatge...")
    
    while True:
        try:
            # Comprova si hi ha dades disponibles per rebre
            if radio.available():
                missatge_recibut = []
                radio.read(missatge_recibut, radio.getDynamicPayloadSize())
                
                # Converteix la llista de bytes a una cadena
                missatge_text = ''.join([chr(b) for b in missatge_recibut if b != 0])
                
                print(f"Missatge rebut: {missatge_text}")
        
        except Exception as e:
            print(f"Error rebent el missatge: {e}")
        
        time.sleep(0.5)  # Evita ocupar massa CPU

else:
    print("Opció no vàlida. Si us plau, escull 'T' per transmissor o 'R' per receptor.")
