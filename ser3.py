#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

import curses 
import time
import pynmea2
import serial
from queue import Queue
from threading import Thread

q = Queue(maxsize=0)

def GUI():
    screen = curses.initscr() 
    curses.noecho() 
    curses.curs_set(0) 
    screen.nodelay(1)
    curses.start_color()

    menu = [\
        ['ttyUSB0', 'ttyUSB1', 'ttyUSB2'],\
        ["4800", "9600", "19200", "38400"]\
    ]
    serialport = 0
    baud = 0
    menucursor = [0,0]
    height, width = screen.getmaxyx()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)#plain
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) #selected
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN) #cursor

    while True: 

        #########Settings menu
        event = screen.getch() 
        if event == ord("q"): break 
        if event == ord("h"):
            menucursor[0] = menucursor[0]-1
            menucursor[0] = max(menucursor[0], 0)
            if menucursor[0] == 0:
                menucursor[1] = serialport
            elif menucursor[0] == 1:
                menucursor[1] = baud
        if event == ord("j"):
            menucursor[1] = menucursor[1]+1
            if menucursor[0] == 0:                      #serial
                menucursor[1] = min(len(menu[0])-1, menucursor[1])
                serialport = menucursor[1]
            elif menucursor[0] == 1:                    #baudrate
                menucursor[1] = min(len(menu[1])-1, menucursor[1])
                baud = menucursor[1]
        if event == ord("k"):
            menucursor[1] = menucursor[1]-1
            if menucursor[0] == 0:                      #serial
                menucursor[1] = max(0, menucursor[1])
                serialport = menucursor[1]
            elif menucursor[0] == 1:                    #baudrate
                menucursor[1] = max(0, menucursor[1])
                baud = menucursor[1]
        if event == ord("l"):
            menucursor[0] = menucursor[0]+1
            menucursor[0] = min(len(menu)-1, menucursor[0])
            if menucursor[0] == 0:
                menucursor[1] = serialport
            elif menucursor[0] == 1:
                menucursor[1] = baud
        for l in range(len(menu)):
            for i in range(len(menu[l])):
                if menucursor == [l,i]:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(3))
                elif(l == 0 and i == serialport): 
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                elif(l == 1 and i == baud): 
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                else:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(1))
#        while not q.empty():
#            screen.addstr(0,0, x.get())
#        screen.refresh()
        screen.addstr(0,0, q.get())
        time.sleep(0.02)

    curses.endwin()
    exit()

def NMEA():
    reader = pynmea2.NMEAStreamReader()
    ser = serial.Serial("/dev/ttyUSB0", baudrate=4800,  timeout=1)
    while(True):
        data = ser.read(16)
        try:
            for msg in reader.next(data.decode("utf-8")):
                q.put(str(msg)) 
        except:
            pass

##########################################
##########################################

tgui = Thread(target=GUI)
tnmea = Thread(target=NMEA)
tgui.start()
tnmea.start()
