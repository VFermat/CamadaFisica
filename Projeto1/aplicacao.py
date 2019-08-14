#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#####################################################
# Camada Física da Computação
# Henry Rocha
# 11/08/2019
# Exemplo de uso do ArgParse e do TkInter.
#####################################################

import sys
import time
import argparse
from enlace import *
from tkinter import Tk
from tkinter.filedialog import askopenfilename



# Serial Com Port
# para saber a sua porta, execute no terminal :
# python -m serial.tools.list_ports

serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411"  # Mac    (variacao de)
#serialName = "COM11"                  # Windows(variacao de)


class Client():

    def __init__(self, serialName, fileName, debug=False):
        self.com = enlace(serialName)
        self.com.enable()
        self.debug = debug
        self.fileName = fileName
        self.results = []
        if debug:
            print("[LOG] Comunicação inicializada.")
            print("[LOG] Porta: {}".format(self.com.fisica.name))
        self.run()

    def run(self):

        self.shouldStop = False
        while not self.shouldStop:
            self.configure(self.fileName)
            if self.fileName != None:
                self.emit()
                self.getResults()
                self.fileName = None
        
        meanImageSize = 0
        meanDeltaTime = 0
        meanTransferRate = 0
        for result in self.results:
            meanImageSize += result[0]
            meanDeltaTime += result[1]
            meanTransferRate += result[2]

        meanImageSize = meanImageSize/len(self.results)
        meanDeltaTime = meanDeltaTime/len(self.results)
        meanTransferRate = meanTransferRate/len(self.results)
        print("[LOG] Tamanho Médio de Imagem.........{:.3f} b".format(meanImageSize))
        print("[LOG] Tempo Médio de Transferência....{:.3f} s".format(meanDeltaTime))
        print("[LOG] Taxa Média de transferência.....{:.3f} b/s".format(meanTransferRate))
        
    def configure(self, fileName):
        
        if fileName is None:
            if self.debug:
                print("\n[LOG] Arquivo não fornecido como argumento, usando GUI.")
            Tk().withdraw() # We don't want a full GUI, so keep the root window from appearing
            fileName = askopenfilename() # Show an "Open" dialog box and return the path to the selected file

            if type(fileName) is tuple or fileName == "":
                self.shouldStop = False
                self.fileName = None
                return None

        with open(fileName, 'rb') as image:
            if self.debug:
                print("[LOG] Arquivo encontrado. Lendo e transformando em bytearray.")
            imageFile = image.read()     
            self.imageByteArray = bytearray(imageFile)
            self.imageSize = bytes(str(len(self.imageByteArray)), 'UTF-8')
            if self.debug:
                print("[LOG] Tamanho do arquivo........{} bytes.".format(int(self.imageSize)))
        
        self.textBuffer = self.imageSize + bytearray(b"start") + self.imageByteArray

    def emit(self):
        if self.debug:
            print("[LOG] Tentado transmitir........{} bytes.".format(len(self.textBuffer)))
        self.startTime = time.time()
        self.com.sendData(self.textBuffer)

        # Esperando o fim da transmissão do arquivo.
        while(self.com.tx.getIsBussy()):
            pass    

        txSize = self.com.tx.getStatus()
        if self.debug:
            print("[LOG] Transmitido...............{} bytes.".format(int(txSize)))
            print("[LOG] Esperando pela resposta do servidor com o tamanho do arquivo.")
        # Esperando pela resposta. Sabemos que ela deve ser o tamanho da arquivo.
        rxBuffer = self.com.getData(len(self.imageSize))[0]
        self.endTime = time.time()
        
        if self.debug:
            print("[LOG] Resposta: {} bytes.".format(int(rxBuffer)))

        # Verifica se o tamanho recebido está correto.
        if int(rxBuffer) != int(self.imageSize):
            if self.debug:
                print("[LOG] Tamanho incorreto.")
            
            # Encerra a comunicação.
            self.com.disable()
            if self.debug:
                print("[LOG] Comunicação encerrada.")
            self.shouldStop = True
            
        if self.debug:
            print("[LOG] Tamanho correto. Arquivo enviado com sucesso.")
            
    def getResults(self):
        deltaTime = self.endTime - self.startTime
        transferRate = int(self.imageSize) / deltaTime
        if self.debug:
            print("[LOG] Tempo levado..............{:.3f} s".format(deltaTime))
            print("[LOG] Taxa de transferência.....{:.3f} b/s".format(transferRate))
        self.results.append([self.imageSize, deltaTime, transferRate])

def client(args):
    # Inicializa enlace... variável COM possui todos os métodos e propriedades do enlace, que funciona em threading
    com = enlace(serialName) # Repare que o metodo construtor recebe um string (nome)
    # Ativa comunicacão
    com.enable()

    # LOG
    print("[LOG] Comunicação inicializada.")
    print("[LOG] Porta: {}".format(com.fisica.name))

    shouldClose = False
    while not shouldClose:
        # Verifica se o arquivo a ser transferido foi passado como
        # argumento ou se deve ser escolhido pelo GUI.
        if args.file is None:
            print("\n[LOG] Arquivo não fornecido como argumento, usando GUI.")
            Tk().withdraw() # We don't want a full GUI, so keep the root window from appearing
            filePath = askopenfilename() # Show an "Open" dialog box and return the path to the selected file
            
            if type(filePath) is tuple or filePath == "":
                shouldClose = True
                sys.exit("[ERRO] Arquivo não escolhido. Abortando... Usar CTRL+C")

        else:
            print("\n[LOG] Arquivo fornecido como argumento.")
            filePath = args.file    
        
        with open(filePath, "rb") as image:
            print("[LOG] Arquivo encontrado. Lendo e transformando em bytearray.")
            imageFile = image.read()
            
            imageByteArray = bytearray(imageFile)

            imageSize = bytes(str(len(imageByteArray)), 'UTF-8')
            print("[LOG] Tamanho do arquivo........{} bytes.".format(int(imageSize)))

        # Criando o buffer a ser transmitido.
        txBuffer = imageSize + bytearray(b"start") + imageByteArray

        # Envia dado.
        print("[LOG] Tentado transmitir........{} bytes.".format(len(txBuffer)))
        startTime = time.time()
        com.sendData(txBuffer)

        # Esperando o fim da transmissão do arquivo.
        while(com.tx.getIsBussy()):
            pass    
        
        # Atualiza dados da transmissão.
        txSize = com.tx.getStatus()
        print("[LOG] Transmitido...............{} bytes.".format(int(txSize)))

        # Esperando pela resposta. Sabemos que ela deve ser o tamanho da arquivo.
        print("[LOG] Esperando pela resposta do servidor com o tamanho do arquivo.")
        rxBuffer, nRx = com.getData(len(imageSize))
        endTime = time.time()

        print("[LOG] Resposta: {} bytes.".format(int(rxBuffer)))

        # Verifica se o tamanho recebido está correto.
        if int(rxBuffer) != int(imageSize):
            print("[LOG] Tamanho incorreto.")
            
            # Encerra a comunicação.
            com.disable()
            print("[LOG] Comunicação encerrada.")
            
        
        print("[LOG] Tamanho correto. Arquivo enviado com sucesso.")

        # Calculando o tempo e a taxa de transferência.
        deltaTime = endTime - startTime
        transferRate = int(imageSize) / deltaTime
        print("[LOG] Tempo levado..............{:.3f} s".format(deltaTime))
        print("[LOG] Taxa de transferência.....{:.3f} b/s".format(transferRate))


    # Encerra a comunicação.
    com.disable()
    print("\n[LOG] Comunicação encerrada.")



def server(args):
    # Inicializa enlace... variável COM possui todos os métodos e propriedades do enlace, que funciona em threading
    com = enlace(serialName) # Repare que o metodo construtor recebe um string (nome)
    # Ativa comunicacão
    com.enable()
   
    # LOG
    print("[LOG] Comunicação inicializada.")
    print("[LOG] Porta: {}".format(com.fisica.name))

    while True:
        # Faz a recepção dos dados
        print("\n[LOG] Recebendo dados...")
        
        keywordRecognized = False
        receiveBuffer = bytearray()
        
        # Espera até receber uma keyword.
        while not keywordRecognized:
            rxBuffer, nRx = com.getData(1)
            receiveBuffer += rxBuffer

            if b"start" in receiveBuffer:
                keywordRecognized = True

        # Cortando a keyword do buffer recebido.
        imageSize = receiveBuffer[:-5]
        print("[LOG] Começou a receber a arquivo. Tamanho do arquivo a ser recebido: {} bytes.".format(int(imageSize)))

        # Agora recebemos a arquivo em si.
        rxBuffer, nRx = com.getData(int(imageSize))

        # Salvando a arquivo recebida.
        with open("receivedImage.png", "wb") as receivedImage:
            receivedImage.write(rxBuffer)

        # LOG
        print("[LOG] Lido....{} bytes ".format(nRx))

        # Retornando o tamanho da arquivo para mostrar que ela foi recebida.
        print("[LOG] Retornando o tamanho do arquivo para mostrar que ele foi recebido.")
        print("[LOG] Tentado transmitir.......{} bytes.".format(len(imageSize)))
        com.sendData(imageSize)

        # Esperando o fim da transmissão do arquivo.
        while(com.tx.getIsBussy()):
            pass    
        
        # Atualiza dados da transmissão.
        txSize = com.tx.getStatus()
        print("[LOG] Transmitido..............{} bytes.".format(int(txSize)))

    # Encerra a cmunicação.
    com.disable()
    print("\n[LOG] Comunicação encerrada.")
    


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Programa que manda e recebe um arquivo usando o Arduino.")
    argParser.add_argument("type", help="Tipo de conexão [client, server].", type=str)
    argParser.add_argument("-f", "--file", help="Arquivo a ser mandado.", type=str)
    argParser.add_argument("-d", "--debug", help="Deve debugar o processo ou não.", type=bool)
    args = argParser.parse_args()

    if args.type == "client":
        client = Client(serialName, args.file, args.debug)
    elif args.type == "server":
        server(args)
    else:
        print("[ERRO] Tipo de conexão inválido.")
