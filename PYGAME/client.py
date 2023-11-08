import pygame as pg
import socket

pg.init()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("localhost", 55555)) # Connect to server
client.setblocking(False) # Prevent socket from waiting for input

W, H = 640, 480
FLAGS = 0

screen = pg.display.set_mode((W, H), FLAGS)
W, H = screen.get_size()

font = pg.font.SysFont("arial", 30)

text = ""

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            running = False

    try:
        raw = client.recv(1024)
    except BlockingIOError:
        pass # No new data. Reuse old data
    else:
        text = raw.decode("utf-8") # New data has arrived. Use it

    screen.fill((0, 0, 0))
    img = font.render(text, True, (255, 255, 255))
    r = img.get_rect(center=(W // 2, H // 2))
    screen.blit(img, r)
    pg.display.update()