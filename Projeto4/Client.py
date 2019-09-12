import os
import time
from Common import Common
from math import ceil
from tkinter import Tk
from tkinter.filedialog import askopenfilename



class Client(Common):  
    def __init__(self, serialName, debug):
        """
        Executed when the object is created. Used to create all needed attributes.
        """
        super().__init__(serialName, debug)

        self.expectedPayloadSize = 0
        self.serverAddress = 0xA0

        self.createCOM(serialName, "client")
        self.run()
        

    def run(self):
        """
        Runs all the logic needed to send a file and receive a response.
        """

        stop = False
        while not stop:
            self.permission = False

            self.getFile()

            self.checkBytes()

            while not self.permission:
                self.sendType1()
                self.waitForType2()

            self.sendFile()

            self.log("File sent sucessfully.", "client")


    def checkBytes(self):
        """
        Goes through all the bytes of the file, fileName, fileExtension and fileSize
        checking if they contain the EOP.
        """

        if self.eop in self.fileBA:            
            oldSize = len(self.fileBA)

            self.fileBA = self.fileBA.replace(self.eop, self.stuffedEOP)
            
            newSize = len(self.fileBA)
            self.expectedPayloadSize = newSize - oldSize


    def buildHead(self):
        """
        Builds the head of the packet.
        """

        # Transforming all the header info into bytes
        msgType = self.msgType3.to_bytes(1, "little")
        serverAddress = self.serverAddress.to_bytes(1, "little")
        currentPacket = self.currentPacket.to_bytes(3, "little")
        totalPackets = self.numberOfPackets.to_bytes(3, "little")
        payloadSize = len(self.payload).to_bytes(1, "little")
        filler = bytes([0]) * 7

        # Build header
        # HEAD[16] = msgType[1] + serverAddress[1] + currentPacket[3] + totalPackets[3] + payloadSize[1]
        self.head = msgType + serverAddress + currentPacket + totalPackets + payloadSize + filler


    def getFile(self):
        """
        Returns info about the selected file.
        """

        Tk().withdraw()
        self.filePath = askopenfilename()

        if (type(self.filePath) is tuple or self.filePath == ""):
            self.log("[ERROR] No file selected. Aborting.", "client")
            self.com.disable()
            exit(0)

        self.log("Selected file: {}".format(self.filePath), "client")

        self.fileName, self.fileExtension = os.path.splitext(self.filePath.split("/")[-1])

        # Checks if the fileName if larger than 15 characters.
        if (len(self.fileName) > 15):
            self.log("[ERROR] File name longer than 15 characters.", "client")
            self.com.disable()
            exit(0)

        self.fileNameBA = bytes(self.fileName, "UTF-8")
        self.fileExtensionBA = bytes(self.fileExtension, "UTF-8")

        try:
            with open(self.filePath, "rb") as file:
                fileInfo = file.read()
                self.fileBA = bytearray(fileInfo)
        except:
            self.log("[ERROR] Could not get the byte array of the selected file. Verify if the file exists.", "client")
            self.com.disable()
            exit(0)

        self.fileSize = len(self.fileBA)
        self.fileSizeBA = self.fileSize.to_bytes(4, "little")
        self.log("File size: {} bytes".format(self.fileSize), "client")

        self.numberOfPackets = ceil(len(self.fileBA) / 128)
        self.currentPacket = 1
    

    def sendType1(self):
        """
        Builds the TYPE 1 message, requesting the server for permission to send data.
        """

        # Transforming all the header info into bytes
        msgType = self.msgType1.to_bytes(1, "little")
        serverAddress = self.serverAddress.to_bytes(1, "little")
        totalPackets = self.numberOfPackets.to_bytes(3, "little")
        fileExtension = bytes("".join(["@" for i in range(5 - len(self.fileExtension))]), "UTF-8") + self.fileExtensionBA
        payloadSize = bytes([0])
        filler = bytes([0]) * 5

        # Build header
        # HEAD = msgType[1] + serverAddress[1] + totalPackets[3] + fileExtension[5] + payloadSize[1] + filler[5]
        head = msgType + serverAddress + totalPackets + payloadSize + fileExtension + filler

        # Sending the request
        self.com.sendData(head + self.eop)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        self.log("Sent TYPE1.", "client")


    def waitForType2(self):
        """
        Waits for a TYPE 2 message from the server, telling the client it
        can start sending data.
        """

        # Wait for response.
        self.log("Waiting for TYPE2.", "client")
        self.response, self.responseSize = self.com.getData(16 + len(self.eop), 5)

        # Response size is 0 if it gets timedout.
        if self.responseSize != 0:
            # Parses the response.
            self.responseMsgType = int.from_bytes(self.response[:1], "little")
            self.responseFiller = self.response[1:]
            
            if self.responseMsgType == self.msgType2:
                self.log("Received TYPE2.", "server")
            
                self.permission = True


    def sendFile(self):
        """
        Sends the file to the server using a TYPE 3 message.
        """

        while self.currentPacket <= self.numberOfPackets:
            # Slicing the file to create the payload
            self.payload = self.fileBA[(self.currentPacket - 1)*128 : self.currentPacket*128]
            
            # Building the header
            self.buildHead()

            # Assemble the packet.
            self.packet = self.head + self.payload + self.eop

            startTime = time.time()
            self.receivedResponse = False
            while not self.receivedResponse:
                # Send the data.
                self.com.sendData(self.packet)

                # Wait for the data to be sent.
                while (self.com.tx.getIsBussy()):
                    pass

                self.log(f"Sent TYPE3. Packet {self.currentPacket}/{self.numberOfPackets}.", "client")

                # Wait for response
                self.log(f"Waiting for TYPE4.", "client")
                self.response, self.responseSize = self.com.getData(16 + 0 + len(self.eop), 5)

                if self.responseSize != 0:
                    self.parseResponse()
                    self.receivedResponse = True

                # Get current timer
                now = time.time()

                # Checking if we had a timeout
                if now - startTime >= 20:
                    self.sendType5(self.currentPacket, self.numberOfPackets)
                    self.com.disable()
                    exit()


    def parseResponse(self):
        """
        Parses the response message, which indicates whether the last
        packet was ok or not.
        """

        self.responseMsgType = int.from_bytes(self.response[:1], "little")
        self.responseLastPacket = int.from_bytes(self.response[1:4], "little")
        self.responsePayloadSize = int.from_bytes(self.response[4:5], "little")
        self.responseFiller = self.response[5:]

        if self.responseMsgType == self.msgType6:
            self.log(f"[ERROR] Packet {self.responseLastPacket} was invalid. Resending...", "client")
            self.currentPacket = self.responseLastPacket + 1
        
        elif self.responseMsgType == self.msgType5:
            self.log(f"Timeout on packet {self.responseLastPacket}. Aborting...", "client")
            self.com.disable()
            exit(1)

        elif self.responseMsgType == self.msgType4:
            self.currentPacket += 1

        else:
            print(f"[ERROR] Unknown message type: {self.responseMsgType}")
