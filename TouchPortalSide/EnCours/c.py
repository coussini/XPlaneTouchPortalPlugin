import socket


def run_client():
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_ip = "127.0.0.1"  # replace with the server's IP address
    server_port = 1234  # replace with the server's port number
    # establish connection with server
    client.connect((server_ip, server_port))

    try:
        while True:close
        close
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
    finally:
        # close client socket (connection to the server)
        client.close()
        print("Connection to server closed")


run_client()