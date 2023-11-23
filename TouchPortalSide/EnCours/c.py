import socket

def run_client():
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 65432
    # establish connection with server
    client.connect((HOST, PORT))

    try:
        while True:
            # get input message from user and send it to the server
            msg = input("Enter message: ")
            client.send(msg.encode("utf-8")[:1024])

            # receive message from the server
            response = client.recv(1024)
            response = response.decode("utf-8")

            # if server sent us "closed" in the payload, we break out of
            # the loop and close our socket
            if response.lower() == "closed":
                break

            print(f"Received: {response}")
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        # close client socket (connection to the server)
        client.close()
        print("Connection to server closed")
    finally:
        # close client socket (connection to the server)
        client.close()
        print("Connection to server closed")

run_client()