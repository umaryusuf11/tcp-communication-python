from socket import socket
import sys
from lib import decodeJsonResponse, parseParameters, createSocket, recvFile, recvListing, sendFile

# static variables
HOST, PORT, OPERATION, PATH = parseParameters()
MAX_BYTES = 1024  # maxSize of data burst

# try to create socket
try:
    # Creates client socket
    client_socket = createSocket(HOST, int(PORT))
except Exception as e:
    print("There was an error creating the socket: " + str(e))
    sys.exit(1)  # exiting with 1 to indicate error.

# Initailize request
cmd = "init " + str(MAX_BYTES) + " " + OPERATION + " " + PATH + " null"
client_socket.send(cmd.encode("utf-8"))

# recieve headers
headers = decodeJsonResponse(client_socket.recv(MAX_BYTES))
client_socket.close()


# try to create socket
try:
    # Creates client socket
    client_socket = createSocket("", int(PORT))
except Exception as e:
    print("There was an error creating the socket: " + str(e))
    sys.exit(1)  # exiting with 1 to indicate error.

try:

    # Process request
    client_socket.send(headers["nextCmd"].encode("utf-8"))

    # recieve data
    if(OPERATION == "list"):
        data = recvListing(client_socket)

    if(OPERATION == "get"):
        dataStream = recvFile(client_socket)

    if(OPERATION == "put"):
        try:
            f = open(PATH, "rb")
            sendFile(client_socket, f)
        except Exception as e:
            print("An error occurred: " + str(e))
            sys.exit(1)


    # try to create socket
    try:
        # Creates client socket
        client_socket = createSocket("", int(PORT))
    except Exception as e:
        print("There was an error creating the socket: " + str(e))
        sys.exit(1)  # exiting with 1 to indicate error.


    client_socket.send(headers["statusCmd"].encode('utf-8'))
    status = client_socket.recv(MAX_BYTES)
    status = decodeJsonResponse(status)

    if(status["code"] == 200):
        if(OPERATION == "list"):
            for filename in data:
                print(filename)
        if(OPERATION == "get"):
                f = open(PATH, "x")
                f = open(PATH, "wb")
                f.write(dataStream)

    if(PATH == "._PATH_._.NULL__._"):
        PATH = ""
    print("[REQUEST] " + HOST + ":" + str(PORT) + " " + OPERATION + " " + PATH + " status:" + str(status))


except Exception as e:
    print("There was an error: " + str(e))
    sys.exit(1)
finally:
    client_socket.close()
