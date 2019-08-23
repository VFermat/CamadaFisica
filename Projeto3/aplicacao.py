#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#####################################################
# Camada Física da Computação
# Henry Rocha e Vitor Eller
# 18/08/2019
# Send and receice data using packets.
#####################################################

from math import ceil
import os
import time
import struct
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



class Common():
    def __init__(self, serialName, debug):
        """
        Initializes all the attributes.
        """

        self.debug = debug

        self.eopB1 = 213
        self.eopB2 = 214
        self.eopB3 = 215
        self.eopB4 = 216
        self.byteStuff = 0
        self.eop = bytes([self.eopB1]) + bytes([self.eopB2]) + bytes([self.eopB3]) + bytes([self.eopB4])
        self.stuffedEOP = bytes([self.eopB1]) + bytes([self.byteStuff]) + bytes([self.eopB2]) + bytes([self.byteStuff]) + bytes([self.eopB3]) + bytes([self.byteStuff]) + bytes([self.eopB4])

        self.responseCodes = {
            "Success": bytes([190]),
            "Size mismatch": bytes([191]),
            "EOP not found": bytes([192]),
            "EOP in wrong place": bytes([193]),
            "Payload size larger than 128 bytes": bytes([194])
        }

        self.responseCodesInverse = {
            bytes([190]): "Success",
            bytes([191]): "Size mismatch",
            bytes([192]): "EOP not found",
            bytes([193]): "EOP in wrong place",
            bytes([194]): "Payload size larger than 128 bytes"
        }


    def createCOM(self, serialName):
        """
        Creates the COM attributes, which handles access to the serial port.

        TODO use the subprocess module to run 'python -m serial.tools.list_ports'
        and try to connect to the available ports.
        """

        self.log("Trying to establish connection to the serial port.")
        

        try:
            self.com = enlace(serialName)
        except:
            print("[ERROR] Could not connect to the serial port.")
            exit(0)

        self.com.enable()
        self.log("Connection to the serial port established.")
        self.log("Port used: {}".format(self.com.fisica.name))


    def log(self, message):
        """
        This function is used to print messages to the screen
        if the debug argument is given.
        """

        if self.debug:
            print("[LOG] " + message)



class Client(Common):  
    def __init__(self, serialName, debug):
        """
        Executed when the object is created. Used to create all needed attributes.
        """
        super().__init__(serialName, debug)
        
        self.expectedPayloadSize = 0

        self.createCOM(serialName)
        self.run()
        

    def run(self):
        """
        Runs all the logic needed to send a file and receive a response.
        """

        stop = False
        while not stop:
            print()

            self.getFile()

            # Forces byte stuffing
            # self.fileBA = self.eop + self.eop
            # print(self.fileBA)

            self.checkBytes()

            self.numberOfPackets = ceil(len(self.fileBA) / 128)
            self.currentPacket = 1

            while self.currentPacket <= self.numberOfPackets:
                print()

                # Slicing the file to create the payload
                self.payload = self.fileBA[(self.currentPacket - 1)*128 : self.currentPacket*128]
                
                # Building the header
                self.buildHead()

                # Assemble the packet.
                self.packet = self.head + self.payload + self.eop

                self.log("Packet: {}/{}".format(self.currentPacket, self.numberOfPackets))

                # Calculate overhead
                self.overhead = (len(self.packet)) / len(self.fileBA)
                self.log("Overhead: {}%".format(self.overhead))

                # Send the data.
                self.log("Trying to send {} bytes.".format(len(self.packet)))
                self.startTime = time.time()
                self.com.sendData(self.packet)

                # Wait for the data to be sent.
                while (self.com.tx.getIsBussy()):
                    pass

                # Log
                txSize = self.com.tx.getStatus()
                self.log("Sent {} bytes.".format(txSize))

                # Wait for response
                self.log("Waiting for server response")
                self.response, self.responseSize = self.com.getData(31)

                # Getting info from response's header
                self.responseCode = self.response[:1]
                self.responsePayloadSize = int.from_bytes(self.response[30:], "little")

                # Getting response's payload and eop
                self.responsePayload, self.responsePayloadSize = self.com.getData(self.responsePayloadSize + len(self.eop))

                self.endTime = time.time()  
                
                self.log("Response: {}".format(self.responseCodesInverse[self.responseCode]))
                
                self.deltaTime = self.endTime - self.startTime
                self.bytesPerSecond = round(len(self.packet) / self.deltaTime)
                self.log("Time taken: {:.3f} s".format(self.deltaTime))
                self.log("Speed: {} b/s".format(self.bytesPerSecond))

                self.currentPacket += 1


    def checkBytes(self):
        """
        Goes through all the bytes of the file, fileName, fileExtension and fileSize
        checking if they contain the EOP.
        """               

        if self.eop in self.fileNameBA:
            self.log("EOP found in fileName.")

        if self.eop in self.fileSizeBA:
            self.log("EOP found in fileSize.")

        if self.eop in self.fileExtensionBA:
            self.log("EOP found in fileExtension.")

        if self.eop in self.fileBA:
            self.log("EOP found in file. Using byte stuffing.")
            
            oldSize = len(self.fileBA)

            self.fileBA = self.fileBA.replace(self.eop, self.stuffedEOP)
            
            newSize = len(self.fileBA)
            self.expectedPayloadSize = newSize - oldSize

        self.log("Bytes stuffed: {} bytes.".format(self.expectedPayloadSize))


    def buildHead(self):
        """
        Builds the head of the packet.
        """

        # Checks if we need to stuff the fileName.
        filler = "".join(["@" for i in range(15 - len(self.fileName))])
        filler = bytes(filler, "UTF-8")
        self.fileNameBA = filler + bytes(self.fileName, "UTF-8")

        # Checks if we need to stuff the fileExtension.
        filler = "".join(["@" for i in range(5 - len(self.fileExtension))])
        filler = bytes(filler, "UTF-8")
        self.fileExtensionBA = filler + bytes(self.fileExtension, "UTF-8")

        # Update the file size with the number of bytes that were stuffed
        # in the payload.
        self.fileSize = self.fileSize + self.expectedPayloadSize
        self.fileSizeBA = self.fileSize.to_bytes(4, "little")

        self.expectedPayloadSizeBA = self.expectedPayloadSize.to_bytes(1, "little")

        # HEAD size is 31 bytes.
        # HEAD = fileName[15] + fileSize[4] + fileExtension[5] + payloadSize[1] + currentPacket[3] + numberOfPackets[3]
        self.head = self.fileNameBA + self.fileSizeBA + self.fileExtensionBA + len(self.payload).to_bytes(1, "little") + self.currentPacket.to_bytes(3, "little") + self.numberOfPackets.to_bytes(3, "little")


    def getFile(self):
        """
        Returns info about the selected file.
        """

        Tk().withdraw()
        self.filePath = askopenfilename()

        if (type(self.filePath) is tuple or self.filePath == ""):
            print("[ERROR] No file selected. Aborting.")
            self.com.disable()
            exit(0)

        self.log("Selected file: {}".format(self.filePath))

        self.fileName, self.fileExtension = os.path.splitext(self.filePath.split("/")[-1])

        # Checks if the fileName if larger than 15 characters.
        if (len(self.fileName) > 15):
            print("[ERRO] File name longer than 15 characters.")
            self.com.disable()
            exit(0)

        self.fileNameBA = bytes(self.fileName, "UTF-8")
        self.fileExtensionBA = bytes(self.fileExtension, "UTF-8")

        self.log("Getting the byte array of the selected file.")

        try:
            with open(self.filePath, "rb") as file:
                fileInfo = file.read()
                self.fileBA = bytearray(fileInfo)
        except:
            print("[ERROR] Could not get the byte array of the selected file. Verify if the file exists.")
            self.com.disable()
            exit(0)

        self.fileSize = len(self.fileBA)
        self.fileSizeBA = self.fileSize.to_bytes(4, "little")
        self.log("File size: {} bytes".format(self.fileSize))
    


class Server(Common):
    def __init__(self, serialName, debug):
        """
        Executed when the object is created. Used to create all needed attributes.
        """

        self.fileProgress = {}

        super().__init__(serialName, debug)

        self.createCOM(serialName)
        self.run()

    
    def run(self):
        """
        Runs all the logic needed to receive a file and send a response.
        """

        stop = False
        while not stop:
            print()
            self.skip = False

            # Wait for a HEAD to arrive
            self.log("Waiting for HEAD[25]...")
            self.head, self.headSize = self.com.getData(31)
            
            # Splice from HEAD all the info needed
            self.fileNameBA = self.head[:15]
            self.fileSizeBA = self.head[15:19]
            self.fileExtensionBA = self.head[19:24]
            self.expectedPayloadSizeBA = self.head[24:25]
            self.currentPacketBA = self.head[25:28]
            self.numberOfPacketsBA = self.head[28:]

            # Decoding info
            self.fileName = self.fileNameBA.decode("UTF-8").replace("@", "")
            self.fileSize = int.from_bytes(self.fileSizeBA, "little")
            self.fileExtension = self.fileExtensionBA.decode("UTF-8").replace("@", "")
            self.expectedPayloadSize = int.from_bytes(self.expectedPayloadSizeBA, "little")
            self.currentPacket = int.from_bytes(self.currentPacketBA, "little")
            self.numberOfPackets = int.from_bytes(self.numberOfPacketsBA, "little")

            self.log("File name: {}".format(self.fileName))
            self.log("File size: {}".format(self.fileSize))
            self.log("File extension: {}".format(self.fileExtension))
            self.log("Expected payload size: {} bytes".format(self.expectedPayloadSize))
            self.log("Packet: {}/{}".format(self.currentPacket, self.numberOfPackets))

            # Getting the payload
            self.payload, self.payloadSize = self.com.getData(self.expectedPayloadSize + len(self.eop))

            # Checking if the payload has the correct size
            if self.expectedPayloadSize != len(self.payload) - len(self.eop):
                print("[ERROR] Payload size larger than 128 bytes.")
                self.respond("Payload size larger than 128 bytes")
                continue

            self.findEOP()

            if not self.skip:
                self.removeStuffedBytes()

            self.respond("Success")

            self.saveFile()

    
    def findEOP(self):
        """
        Tries to find the EOP in the payload.
        """

        if self.eop in self.payload:
            self.log("EOP found in payload. Removing it.")
        else:
            print("[ERROR] Could not find EOP in payload.")
            self.respond("EOP not found")
            self.skip = True
            return

        index = self.payload.find(self.eop)
        self.payload = self.payload[:index]

        leftover = self.payload[index + len(self.eop):]
        if len(leftover) > 0:
            self.respond("EOP in wrong place")
            self.skip = True
            return
            
        self.log("EOP located in byte: {}".format(index))


    def removeStuffedBytes(self):
        """
        Goes through the payload checking if the was byte stuffing.
        """

        # Checking every three bytes to see if they match the first three bytes
        # of the EOP, if they do, we remove the 0x00 after them.
        self.log("Removing stuffed bytes.")
        self.payload = self.payload.replace(self.stuffedEOP, self.eop)
        

    def respond(self, message):
        """
        Sends a response to the client.
        """

        self.log("Response: {}".format(message))
        self.responseBA = self.responseCodes[message]
        zero = 0
        self.response = self.responseBA + zero.to_bytes(30, "little") + self.eop

        # Send the data.
        self.log("Trying to send {} bytes.".format(len(self.responseBA)))
        self.com.sendData(self.response)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        txSize = self.com.tx.getStatus()
        self.log("Sent {} bytes.".format(txSize))


    def saveFile(self):
        """
        Saves the received file.
        """

        if self.fileName not in self.fileProgress:
            self.fileProgress[self.fileName] = {
                "name" : self.fileName,  
                "extension" : self.fileExtension,
                "size" : self.fileSize,
                "currentPacket" : self.currentPacket,  
                "totalPackets" : self.numberOfPackets,
                "file" : self.payload
            }
        else:
            if self.currentPacket == self.fileProgress[self.fileName]["currentPacket"] + 1:
                self.fileProgress[self.fileName]["file"] += self.payload
                self.fileProgress[self.fileName]["currentPacket"] = self.currentPacket
                self.log("File progress updated.")
            else:
                self.log("Packet already received.")

            if self.fileProgress[self.fileName]["currentPacket"] == self.fileProgress[self.fileName]["totalPackets"]:
                with open("received_" + self.fileName + self.fileExtension, "wb") as filea:
                    filea.write(self.fileProgress[self.fileName]["file"])

                self.log("File saved.")



if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Program to send and receive data using the Arduino Due.")
    argParser.add_argument("type", help="Type of connection [client, server].", type=str)
    argParser.add_argument("-d", "--debug", help="Debug mode.", action="store_true")
    args = argParser.parse_args()

    if args.type == "client":
        client = Client("/dev/ttyACM1", args.debug)
    elif args.type == "server":
        server = Server("/dev/ttyACM0", args.debug)
    else:
        print("[ERRO] Invalid connection type.")