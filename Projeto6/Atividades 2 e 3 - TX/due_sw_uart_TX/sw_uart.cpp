#include "sw_uart.h"
#pragma GCC optimize ("-O3")

void sw_uart_setup(due_sw_uart *uart, int rx, int tx, int stopbits, int databits, int paritybit, int baudrate) {
	uart->pin_tx     = tx;
	uart->pin_rx     = rx;
	uart->stopbits   = stopbits;
	uart->paritybit  = paritybit;
  uart->databits   = databits;
  uart->baudrate   = baudrate;
  pinMode(rx, INPUT);
  pinMode(tx, OUTPUT);
  digitalWrite(tx, HIGH);
}

void sw_uart_write_data(due_sw_uart *uart, char* bufferData, int writeN) {
  for(int i = 0; i < writeN; i++) {
    sw_uart_write_byte(uart, bufferData[i]);
  }
}

void sw_uart_write_string(due_sw_uart *uart, char* stringData) {
  sw_uart_write_data(uart, stringData, strlen(stringData));
}

int calc_even_parity(char data) {
  int ones = 0;

  for(int i = 0; i < 8; i++) {
    ones += (data >> i) & 0x01;
  }

  return ones % 2;
}

int sw_uart_receive_byte(due_sw_uart *uart, char* data) {
  // wait start bit
  while(digitalRead(uart->pin_rx) == HIGH);

  // confirm start bit
  _sw_uart_wait_half_T(uart);
  // HIGH = invalid
  if(digitalRead(uart->pin_rx) == HIGH) {
    return SW_UART_ERROR_FRAMING;
  }

  _sw_uart_wait_T(uart);
  
  // start getting data 
  char aux = 0x00;
  for(int i = 0; i < uart->databits; i++) {
    aux |= digitalRead(uart->pin_rx) << i;
    _sw_uart_wait_T(uart);
  }
  
  // parity
  int rx_parity = 0;
  if(uart->paritybit != SW_UART_NO_PARITY) {
    rx_parity = digitalRead(uart->pin_rx);
    _sw_uart_wait_T(uart);
  }

  // get stop bit
  for(int i = 0; i < uart->stopbits; i++) {
    if(digitalRead(uart->pin_rx) == LOW) {
      return SW_UART_ERROR_FRAMING;
    }
    _sw_uart_wait_T(uart);
  }
  
  int parity = 0;
  if(uart->paritybit == SW_UART_EVEN_PARITY) {
     parity = calc_even_parity(aux);
  } else if(uart->paritybit == SW_UART_ODD_PARITY) {
     parity = !calc_even_parity(aux);
  }

  if(parity != rx_parity) {
    return SW_UART_ERROR_PARITY;
  }
  
  *data = aux;
  return SW_UART_SUCCESS;
}

void sw_uart_write_byte(due_sw_uart *uart, char data) {
  // send parity
  int parity = 0;

  if(uart->paritybit == SW_UART_EVEN_PARITY) {
     parity = calc_even_parity(data);
  } else if(uart->paritybit == SW_UART_ODD_PARITY) {
     parity = !calc_even_parity(data);
  }
  
  // send start bit
  digitalWrite(uart->pin_tx, LOW);
  _sw_uart_wait_T(uart);

  // Force framing error
  //_sw_uart_wait_half_T(uart);
  
  // start sending data
  for(int i = 0; i < uart->databits; i++) {
    digitalWrite(uart->pin_tx, (data >> i) & 0x01);
    _sw_uart_wait_T(uart);
  }

  if(uart->paritybit != SW_UART_NO_PARITY) {
    digitalWrite(uart->pin_tx, parity);

    // Force parity error
    //digitalWrite(uart->pin_tx, LOW);
    
    _sw_uart_wait_T(uart);  
  }
  
  // send stop bit
  for(int i = 0; i < uart->stopbits; i++) {
    digitalWrite(uart->pin_tx, HIGH);
    
    // Force stopbit error
    //digitalWrite(uart->pin_tx, LOW);
    
    _sw_uart_wait_T(uart);
  }
}

// MCK 21MHz
void _sw_uart_wait_half_T(due_sw_uart *uart) {
   for(int i = 0; i < 21000000/(2*uart->baudrate); i++) {
      asm("NOP");
   }
  
//  for(int i = 0; i < 1093; i++)
//    asm("NOP");
}

void _sw_uart_wait_T(due_sw_uart *uart) {
  _sw_uart_wait_half_T(uart);
  _sw_uart_wait_half_T(uart);
}
