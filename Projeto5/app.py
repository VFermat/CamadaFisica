#####################################################
# Camada Física da Computação
# Henry Rocha e Vitor Eller
# 18/08/2019
# Send and receice data using packets.
#####################################################



import argparse
from Client import Client
from Server import Server



if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Program to send and receive data using the Arduino Due.")
    argParser.add_argument("type", help="Type of connection [client, server].", type=str)
    argParser.add_argument("-d", "--debug", help="Debug mode.", action="store_true")
    args = argParser.parse_args()

    # Serial Com Port
    # para saber a sua porta, execute no terminal:
    # python -m serial.tools.list_ports

    serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
    #serialName = "/dev/tty.usbmodem1411"  # Mac    (variacao de)
    #serialName = "COM11"                  # Windows(variacao de)

    if args.type == "client":
        client = Client("/dev/ttyACM1", args.debug)
    elif args.type == "server":
        server = Server("/dev/ttyACM0", args.debug)
    else:
        print("[ERROR] Invalid connection type.")