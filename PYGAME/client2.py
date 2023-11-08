import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("localhost", 55555)) # Connect to server
client.setblocking(False) # Prevent socket from waiting for input
text = ""

running = True
while running:
    try:
        raw = client.recv(1024)
    except BlockingIOError:
        pass # No new data. Reuse old data
    else:
        text = raw.decode("utf-8") # New data has arrived. Use it
    if text != "":
        print(f"le texte est {text}")