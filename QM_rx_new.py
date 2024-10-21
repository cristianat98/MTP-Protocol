import time
import board
from digitalio import DigitalInOut
from circuitpython_nrf24l01.rf24 import RF24

# Configuración SPI para Raspberry Pi
import spidev

# Configuración de pines
SPI_BUS = spidev.SpiDev()
CSN_PIN = 0  # Usar CE0 (GPIO8) para CSN en Raspberry Pi
CE_PIN = DigitalInOut(board.D22)  # Usar GPIO22 para CE

# Inicializar el módulo nRF24L01
nrf = RF24(SPI_BUS, CSN_PIN, CE_PIN)

def check_connection():
    # Verificar si el módulo responde leyendo el registro de configuración (0x00)
    config_reg = nrf.read_register(0x00)

    # Si el módulo está conectado correctamente, debería devolver un valor distinto de 0xFF
    if config_reg == 0xFF:
        print("ERROR: No se ha detectado el módulo nRF24L01. Verifica las conexiones.")
    else:
        print(f"Conexión exitosa. Valor del registro de configuración: {config_reg:#02x}")

    # Probar escritura/lectura de un registro para verificar comunicación completa
    test_value = 0x0F
    nrf.write_register(0x05, test_value)  # Cambia el canal para testear escritura
    read_value = nrf.read_register(0x05)

    if read_value == test_value:
        print(f"Prueba de escritura/lectura exitosa. Valor leído: {read_value:#02x}")
    else:
        print(f"ERROR: Valor leído {read_value:#02x} no coincide con valor escrito {test_value:#02x}")

try:
    print("Comprobando conexión con el transceiver nRF24L01...")
    check_connection()
except Exception as e:
    print(f"ERROR: {e}")
finally:
    # Apagar el transceptor
    nrf.power = False
