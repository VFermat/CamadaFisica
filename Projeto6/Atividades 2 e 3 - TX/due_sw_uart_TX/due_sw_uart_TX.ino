#include "sw_uart.h"

due_sw_uart uart;
int baudrate = 9600;

void setup() {
  Serial.begin(baudrate);
  sw_uart_setup(&uart, 4, 3, 1, 8, SW_UART_EVEN_PARITY, baudrate);
}

void loop() {
 test_write();
}

void test_write() {
  sw_uart_write_string(&uart,"a");
  delay(1000);
}
