import RPi.GPIO as GPIO
import nrf24
import spidev
from receiver import receiver
from .transmitter import transmitter

if __name__ == "__main__":
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

    # TODO: How to get the device type
    type_device = "transmitter"

    if type_device == "transmitter":
        transmitter(radio)
    else:
        receiver(radio)

    GPIO.cleanup()  # Netejar els pins GPIO després d'utilitzar
