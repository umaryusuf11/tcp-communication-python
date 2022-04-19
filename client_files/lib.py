""" USES python3 syntax to allow for parameter types e.g. add(num1:int, num2:int): """
import io
import socket
import sys
import os
import json
import math
import uuid  # used to generate sessionID


""" Sessions Handling """
SESSIONS = {

}


def generateSession(maxBytes: int, operation: str, path: str) -> dict:
    """ Initializes New Session and returns it """
    sessionID = str(uuid.uuid1())
    nextCmd = "process " + str(maxBytes) + " " + \
        operation + " " + path + " " + sessionID
    statusCmd = "status " + str(maxBytes) + " " + \
        operation + " " + path + " " + sessionID
    headers = {
        "sessionID": sessionID,
        "operation": operation,
        "nextCmd": nextCmd,
        "path": path,
        "status": "",
        "statusCmd": statusCmd
    }
    SESSIONS[sessionID] = headers
    return SESSIONS[sessionID]


def getSession(sessionID: str) -> dict:
    """ Returns the session with the given ID """
    return SESSIONS[sessionID]


def deleteSession(sessionID: str):
    """ Terminates a session """
    return SESSIONS.pop(sessionID, None)  # using this instead of del so it doesnt crash if session doesnt exist


def setStatus(sessionID: str, status: dict):
    """ sets the status of a session """
    SESSIONS[sessionID]["status"] = status


def getStatus(sessionID: str) -> str:
    """ Get the status of a session """
    return SESSIONS[sessionID]["status"]


""" Data Parsing """


def parseParameters():
    """ Parses cli arguments into array [HOST,PORT,OPERATION,PATH] """
    try:
        HOST = sys.argv[1]
        PORT = sys.argv[2]
        OPERATION = sys.argv[3]
        PATH = "._PATH_._.NULL__._"
        if(OPERATION == "put" or OPERATION == "get"):
            PATH = sys.argv[4]
        return[HOST, int(PORT), OPERATION, PATH]
    except Exception as e:
        print("There was an error: Required parameters not entered")
        sys.exit(1)


def parseCommand(cmd: str):
    """ Parse a server command and return as an array [STAGE, MAX_BYTES, OPERATION, PATH] """
    STAGE = cmd.split(" ")[0]
    MAX_BYTES = cmd.split(" ")[1]
    OPERATION = cmd.split(" ")[2]
    PATH = cmd.split(" ")[3]
    sessionID = cmd.split(" ")[4]
    return [STAGE, int(MAX_BYTES), OPERATION, PATH, sessionID]


""" Data Conversion """


def parseArray(arrayString):
    """ Server responds in bytes that are then converted to strings with .decode(). This parses an array in string form back into a normal array """
    return arrayString.strip("][").split(", ")


def decodeJsonResponse(res: bytes) -> dict:
    """ decodes bytes and loads into a dictionary """
    return json.loads(res.decode("utf-8"))


def encodeJsonResponse(res: dict):
    """ turns dict to string and encodes to bytes """
    return json.dumps(res).encode("utf-8")


""" Network """


def createSocket(host: str, port: int, isServer: bool = False, maxQeueSize: int = 5):
    """ Creates and returns a socket.socket object with given variables """
    # socket.AF_INET indicates using IPv4 and SOCK_STREAM indicates using TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if(isServer):
        # bind the socket on host:port
        sock.bind((host, port))
        # Start listening for up to maxSize consequtive requests made to the server
        sock.listen(maxQeueSize)
        return sock
    else:
        # since its not a server its a client
        sock.connect((host, port))
        return sock


def sendStatus(sock: socket.socket, sessionID: str):
    status = getStatus(sessionID)
    sock.send(encodeJsonResponse(status))


def sendListing(sock: socket.socket, sessionID: str):
    data = str(os.listdir())  # same as ls in terminal
    # convert string to bytesIO so I can seek in case string is bigger than 1024 bytes
    dataStream = io.BytesIO(data.encode('utf-8'))
    data = dataStream.read(1024)
    while (data):
        sock.send(data)
        data = dataStream.read(1024)
    setStatus(sessionID, {"code": 200, "msg": "ok"})


def recvListing(sock: socket.socket):
    dataStream = io.BytesIO()  # initialize bytesIO
    data = sock.recv(1024)
    while(data):
        dataStream.seek(0, 2)  # move to the end
        dataStream.write(data)
        data = sock.recv(1024)
    return parseArray(dataStream.getvalue().decode('utf-8'))


def sendFile(sock: socket.socket, f: io.BytesIO):
    data = f.read(1024)
    while (data):
        sock.send(data)
        data = f.read(1024)


def recvFile(sock: socket.socket):
    dataStream = io.BytesIO()  # initialize bytesIO
    data = sock.recv(1024)
    while(data):
        dataStream.seek(0, 2)  # move to the end
        dataStream.write(data)
        data = sock.recv(1024)
    return dataStream.getvalue()


def handleProcess(cliSock: socket.socket, operation: str, path: str, sessionID: str):
    status = {
        "code": 200,
        "msg": "ok"
    }

    try:
        if(operation == "list"):
            sendListing(cliSock, sessionID)
        if(operation == "get"):
            f = open(path, "rb")
            sendFile(cliSock, f)
            setStatus(sessionID, {"code": 200, "msg": "ok"})
        if(operation == "put"):
            data = recvFile(cliSock)
            f = open(path, "x")
            f = open(path, "wb")
            f.write(data)
            setStatus(sessionID, {"code": 200, "msg": "ok"})

    except Exception as e:
        status = {
            "code": 400,
            "msg": str(e)
        }
        data = encodeJsonResponse(status)
        setStatus(sessionID, status)
        cliSock.send("".encode('utf-8'))
