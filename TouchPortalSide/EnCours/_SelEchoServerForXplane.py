import selectors
import socket
import json
import random

mysel = selectors.DefaultSelector()
keep_running = True
list_connections = []

def get_dataref_name_and_index(dataref):
    
    """
    receive a dataref from a JSON
    theres examples of dataref names including or not an index
    'sim/aircraft/electrical/num_batteries'
    'sim/multiplayer/combat/team_status[3]' the index is 3
    """

    dataref_index = None 
    dataref_name = dataref.replace("["," ")
    dataref_name = dataref_name.replace("]"," ")
    dataref_name = dataref_name.split()

    # it's a dataref with an index
    if len(dataref_name) == 2: 
        dataref_index = dataref_name[1]
        dataref_name = dataref_name[0]
    
    # it's not a dataref with an index
    else: 
        dataref_name = dataref_name[0]

    return dataref_name,dataref_index 

def init_command(data):

    print("--> INIT section")
    for x in data["datarefs"]:
        dataref_name,dataref_index = get_dataref_name_and_index(x['dataref'])
        print(f"Dataref name = {dataref_name} and dataref index = {dataref_index}")
        x['value'] = str(random.randrange(0,5))

    return data

def write_command(data):

    print("--> WRITE section")

def reception(data):

    send_data = None

    command = data["command"]
    match command:
        case "init":
            send_data = init_command(data)
        case "write":
            send_data = write_command(data)
        case _:
            print('This command is not recognized by the server')

    return send_data

def read(connection, mask):
    #Callback for read events
    global keep_running

    data = connection.recv(1024)
    if not data:
        print("No data")
        keep_running = False
    else:
        # transforming byte to json format
        mydata = data.decode()
        mydata_json = json.loads(mydata)
        send_data = reception(mydata_json)
        send_data_encode = json.dumps(send_data).encode()
        connection.sendall(send_data_encode)

def accept(sock, mask):
    #Callback for new connections
    new_connection, addr = sock.accept()
    list_connections.append(new_connection) 
    new_connection.setblocking(False)
    mysel.register(new_connection, selectors.EVENT_READ, read)


try:
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 65432
    print(f'starting X-Plane server on {HOST},{PORT}')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.bind((HOST,PORT))
    server.listen(5)

    mysel.register(server, selectors.EVENT_READ, accept)

    while keep_running:
        print('waiting for I/O')
        for key, mask in mysel.select(timeout=1):
            callback = key.data
            callback(key.fileobj, mask)

    for connection in list_connections:
        mysel.unregister(connection)
        connection.close()
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    print('shutting down')
    mysel.close()