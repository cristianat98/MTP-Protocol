import RPi.GPIO as GPIO
import nrf24

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

type_device = "transmitter"

if type_device == "transmitter":
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
else:
  receptor_nrf24()
GPIO.cleanup()  # Netejar els pins GPIO després d'utilitzar
