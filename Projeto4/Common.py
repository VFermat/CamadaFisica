from enlace import enlace



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

        self.msgType1 = 1
        self.msgType2 = 2
        self.msgType3 = 3
        self.msgType4 = 4
        self.msgType5 = 5
        self.msgType6 = 6


    def createCOM(self, serialName):
        """
        Creates the COM attributes, which handles access to the serial port.

        TODO use the subprocess module to run 'python -m serial.tools.list_ports'
        and try to connect to the available ports.
        """

        self.log("Trying to establish connection to the serial port.", "")
        

        try:
            self.com = enlace(serialName)
        except:
            print("[ERROR] Could not connect to the serial port.")
            exit(0)

        self.com.enable()
        self.log("Connection to the serial port established.", "")
        self.log("Port used: {}".format(self.com.fisica.name), "")


    def log(self, message, caller):
        """
        This function is used to print messages to the screen
        if the debug argument is given.
        """

        if "ERROR" not in message:
            message = "[LOG] " + message
        if self.debug:
            print(message)
            if caller == "client":
                with open("log/client.log", "a") as file:
                    file.write(f"{message}\n")
            elif caller == "server":
                with open("log/server.log", "a") as file:
                    file.write(f"{message}\n")
            else:
                with open("log/client.log", "a") as file:
                    file.write(f"{message}\n")
                with open("log/server.log", "a") as file:
                    file.write(f"{message}\n")


    def sendType5(self):
        """
        Sends a TYPE 5 message, which indicates there was a timeout.
        """

        # Build packet
        packet = self.msgType5.to_bytes(1, "little") + self.eop

        # Sending the request
        self.com.sendData(packet)

        # Wait for the data to be sent.
        while (self.com.tx.getIsBussy()):
            pass

        self.log("Timeout.", "")