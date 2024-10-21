import time
import board
import struct
from digitalio import DigitalInOut
from circuitpython_nrf24l01.rf24 import RF24

# Pines de conexión
ce = DigitalInOut(board.D22)  # GPIO 22 (Pin 15)
csn = DigitalInOut(board.CE0)  # CE0 (GPIO 8, Pin 24)

# Configuración del SPI y el módulo RF24
spi = board.SPI()  # SPI hardware
nrf = RF24(spi, csn, ce)

# Configurar el NRF24L01+
nrf.pa_level = -12  # Potencia baja para evitar interferencias
nrf.channel = 100   # Canal (puedes cambiarlo)
nrf.data_rate = RF24.RATE_1MBPS  # Velocidad de transmisión

# Dirección de prueba
address = [b"1Node", b"2Node"]
nrf.open_tx_pipe(address[0])  # Abrir el pipe de transmisión
nrf.open_rx_pipe(1, address[1])  # Abrir el pipe de recepción

# Detalles del módulo (verificación)
print("Detalles del NRF24L01:")
print("----------------------")
nrf.print_details()

# Función para comprobar conexión
def check_connection():
    nrf.listen = False  # Desactivar la escucha
    test_message = b"ping"
    
    print("Enviando mensaje de prueba: 'ping'")
    result = nrf.send(test_message)
    
    if result:
        print("Mensaje enviado con éxito")
    else:
        print("Fallo al enviar el mensaje")
    
    # Activar escucha para recibir
    nrf.listen = True
    start = time.monotonic()
    
    # Esperar respuesta
    timeout = 2  # segundos
    print("Esperando respuesta...")
    
    while (time.monotonic() - start) < timeout:
        if nrf.any():
            received = nrf.recv()
            print("Respuesta recibida:", received)
            return True
    
    print("No se recibió respuesta.")
    return False

# Ejecutar la función de verificación
if _name_ == "_main_":
    if check_connection():
        print("La conexión entre Raspberry Pi y NRF24L01 es exitosa.")
    else:
        print("No se pudo establecer conexión.")
