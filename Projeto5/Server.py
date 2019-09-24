#####################################################
# Camada Física da Computação
# Henry Rocha e Vitor Eller
# 18/08/2019
# Send and receice data using packets.
#####################################################



import time
from Common import Common
from PyCRC.CRC16 import CRC16



class Server(Common):
    def __init__(self, serialName, debug):
        """
        Executed when the object is created. Used to create all needed attributes.
        """

        self.fileProgress = {}
        self.idle = True
        self.address = 0xA0

        super().__init__(serialName, debug)

        self.createCOM(serialName, "server")
        self.run()

    
    def run(self):
        """
        Runs all the logic needed to receive a file and send a response.
        """

        stop = False
        while not stop:
            self.skip = False

            while self.idle:
                self.waitForType1()

            self.sendType2()

            self.receiveFile()

    
    def findEOP(self):
        """
        Tries to find the EOP in the payload.
        """

        if self.eop not in self.payload:
            self.log("[ERROR] Could not find EOP in payload.", "server")
            self.sendType6()
            return

        index = self.payload.find(self.eop)
        self.payload = self.payload[:index]

        leftover = self.payload[index + len(self.eop):]
        if len(leftover) > 0:
            self.log("[ERROR] EOP Found in wrong place.", "server")
            self.sendType6()
            return


    def removeStuffedBytes(self):
        """
        Goes through the payload checking if the was byte stuffing.
        """

        # Checking every three bytes to see if they match the first three bytes
        # of the EOP, if they do, we remove the 0x00 after them.
        self.payload = self.payload.replace(self.stuffedEOP, self.eop)

    
    def sendType2(self):
        """
        Send TYPE2 message, which indicates that the server is ready to receive packets.
        """
        
        msgType = self.msgType2.to_bytes(1, "little")
        filler = bytearray([0]) * 15

        self.com.sendData(msgType + filler + self.eop)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        self.log("Sent TYPE2.", "server")


    def waitForType1(self):
        """
        Awaits a TYPE1 message, request permission to start sending packets.
        """

        self.log("Waiting for TYPE1 message...", "server")
        self.request, self.requestSize = self.com.getData(16, 1)

        if self.requestSize != 0:
            self.responseMsgType = int.from_bytes(self.request[:1], "little")
            self.responseServerAddress = int.from_bytes(self.request[1:2], "little")

            if self.responseServerAddress == self.address:
                self.numberOfPackets = int.from_bytes(self.request[2:5], 'little')
                self.fileExtension = self.request[6:11].decode("UTF-8").replace("@", "")
                
                self.fileName = "file"
                self.file = bytes()
                self.currentPacket = 0
                self.expectedPacket = 1

                self.idle = False

                self.log("Received TYPE1.", "server")
            else:
                self.log("TYPE1 message not addressed to this server.", "server")

        self.com.rx.clearBuffer()


    def receiveFile(self):
        """
        Receives TYPE3 messages and responds with TYPE4/TYPE5/TYPE6.
        """

        while self.currentPacket < self.numberOfPackets:
            startTime = time.time()

            received = False
            while not received:
                # Wait for header
                self.log("Waiting for header of TYPE3.", "server")
                self.head, self.headSize = self.com.getData(16, 1)

                # # Check if we received a message
                if self.headSize != 0:
                    self.parseHead()

                    self.payload, self.payloadSize = self.com.getData(self.expectedPayloadSize + len(self.eop), 1)

                    self.parsePayload()

                    self.updateFileProgress()

                    self.sendType4()

                    received = True

                if time.time() - startTime > 20:
                    self.sendType5(self.currentPacket, self.numberOfPackets)
                    self.idle = True
                    return

                if time.time() - startTime > 2:
                    self.sendType4()


    def parseHead(self):
        """
        Parses the received TYPE3 message header.
        """

        self.receivedMsgType = int.from_bytes(self.head[:1], "little")
        if self.receivedMsgType != self.msgType3:
            self.log(f"[ERROR] Invalid message type. Expected type 3 and received type {self.receivedMsgType}.", "server")
            self.sendType6()
            return

        self.receivedServerAddress = int.from_bytes(self.head[1:2], "little")
        if self.receivedServerAddress != self.address:
            self.log(f"[ERROR] Wrong server address. Client trying to send to {self.receivedServerAddress}. This server runs on address {self.address}.", "server")
            self.sendType6()
            return

        self.currentPacket = int.from_bytes(self.head[2:5], "little")
        self.expectedPayloadSize = int.from_bytes(self.head[8:9], "little")
        self.filler = self.head[9:16]

        self.log(f"Packet: {self.currentPacket}/{self.numberOfPackets}", "server")


    def parsePayload(self):
        """
        Parses the received TYPE3 message payload and eop.
        """

        # Checking if the payload has the correct size
        if self.expectedPayloadSize != len(self.payload) - len(self.eop):
            self.sendType6()
            self.log(f"[ERROR] Received payload size is wrong. Please send it again.", "server")
            return

        self.findEOP()

        self.checkCrc()
        self.payload = self.payload[:-2]
        
        self.removeStuffedBytes()

    
    def checkCrc(self):
        """
        Checks if message is correct
        """
        
        crc = CRC16().calculate(bytes(self.payload))
        if crc != 0:
            self.log("[ERROR] Wrong CRC.", "server")
            self.sendType6()
            return


    def sendType6(self):
        """
        Sends a TYPE6 message to the client, indicating there was an error with the last packet.
        """

        # Build header parts.
        msgType = self.msgType6.to_bytes(1, "little")
        lastPacket = self.currentPacket.to_bytes(3, "little")
        payloadSize = bytes([0])
        filler = bytes([0]) * 11

        # Send message.
        self.com.sendData(msgType + lastPacket + payloadSize + filler + self.eop)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        self.com.rx.clearBuffer()
        self.log(f"Sent TYPE6. Expected packet is {self.expectedPacket}", "server")


    def sendType4(self):
        """
        Send TYPE4 message, informing the client the last packet was ok.
        """

        # Build header parts.
        msgType = self.msgType4.to_bytes(1, "little")
        lastPacket = self.currentPacket.to_bytes(3, "little")
        payloadSize = bytes([0])
        filler = bytes([0]) * 11

        # Send message.
        self.com.sendData(msgType + lastPacket + payloadSize + filler + self.eop)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        self.log("Sent TYPE4.", "server")


    def updateFileProgress(self):
        """
        Saves the received file.
        """

        if self.currentPacket == self.expectedPacket:
            self.file += self.payload
            self.expectedPacket += 1
        else:
            self.log(f"Expected packet {self.expectedPacket}. Received {self.currentPacket}", "server")
            self.sendType6()

        if self.currentPacket == self.numberOfPackets:
            with open("received_" + self.fileName + self.fileExtension, "wb") as filea:
                filea.write(self.file)

            self.currentPacket = self.numberOfPackets
            self.idle = True

            self.log("File saved.", "server")