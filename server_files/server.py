import socket
import sys
import os
from lib import createSocket, deleteSession, encodeJsonResponse, generateSession, getSession, getStatus, handleProcess, parseCommand

# try to create socket
try:
    # Creates a socket on the server side
    server_socket = createSocket("", int(sys.argv[1]), True, 5)

    print("server up and running on localhost:" + sys.argv[1])

    """ Infinte Loop """
    while True:
        # socket.accept() returns a tuple. this destructures the tuple into 2 variables
        client_socket, client_address = server_socket.accept()
        # converting client_address object to a string
        client_address_str = str(client_address[0])
        client_port_str = str(client_address[1])

        request = client_socket.recv(1024)  # receive init command from client
        cmd = request.decode("utf-8")

        # parse cmd
        STAGE, MAX_BYTES, OPERATION, PATH, SESSION_ID = parseCommand(cmd)

        if(STAGE == "init"):
            headers = generateSession(MAX_BYTES, OPERATION, PATH)
            client_socket.send(encodeJsonResponse(headers))
        if(STAGE == "process"):
            # handle process and send res.
            handleProcess(client_socket, OPERATION, PATH, SESSION_ID)
            status = getStatus(SESSION_ID)
            #log status
            if(PATH == "._PATH_._.NULL__._"):
                PATH = ""
            print("[REQUEST] " + client_address_str + ":" + client_port_str + " " + OPERATION + " " + PATH + " status:" + str(status))
        if(STAGE == "status"):
            status = getStatus(SESSION_ID)
            client_socket.send(encodeJsonResponse(status))
            deleteSession(SESSION_ID)

        client_socket.close()

except Exception as e:
    print("There was an error starting the server: " + str(e))
    sys.exit(1)