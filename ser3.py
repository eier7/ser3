#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

import curses 
import time
import pynmea2
import serial
from queue import Queue
from threading import Thread

parsednmea = Queue(maxsize=0)
serialsettings= Queue(maxsize=0)
rawdata = Queue(maxsize=0)

def GUI():
    screen = curses.initscr() 
    curses.noecho() 
    curses.curs_set(0) 
    screen.nodelay(1)
    curses.start_color()

    menu = [\
        ['ttyUSB0', 'ttyUSB1', 'ttyUSB2'],\
        ['4800', '9600', '19200', '38400']\
    ]
    serialport = 0
    baud = 0
    sentences = []
    menucursor = [0,0]
    height, width = screen.getmaxyx()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)#plain
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) #selected
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN) #cursor
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED) #alarm
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_WHITE) #alarm

    serialsettings.put([menu[0][serialport]+","+menu[1][baud]]) #start serial port

    class sentence:
        def __init__(self, msg, txt):
            self.msgtype = msg
            self.msg = txt


    while True: 
        screen.erase()
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
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif menucursor[0] == 1:                    #baudrate
                menucursor[1] = min(len(menu[1])-1, menucursor[1])
                baud = menucursor[1]
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
        if event == ord("k"):
            menucursor[1] = menucursor[1]-1
            if menucursor[0] == 0:                      #serial
                menucursor[1] = max(0, menucursor[1])
                serialport = menucursor[1]
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif menucursor[0] == 1:                    #baudrate
                menucursor[1] = max(0, menucursor[1])
                baud = menucursor[1]
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
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

        ######nmea display
        found = False
        while not parsednmea.empty():
            msg = parsednmea.get()
            if msg == "ERROR":
                if int(time.time()) % 2 == 0:
                    screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(4))
                else:
                    screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(5))
                    
            else:
                try:
                    msgtype = msg.__dict__['sentence_type']
                except:
                    pass
                for item in sentences:
                    if item.msgtype ==  msgtype:
                        item.msg = msg
                        found = True
                if not found:
                    sentences.append(sentence(msgtype, msg))
        for s in range(len(sentences)):
            screen.addstr(s, 0, str(sentences[s].msg))


        screen.refresh()
        time.sleep(0.1)

    curses.endwin()
    exit()

def NMEA():
    serinit = False
    reader = pynmea2.NMEAStreamReader()
    port = ""
    baud = 0
    while(True):
        if not serialsettings.empty():
            for s in serialsettings.get():
                s = s.split(",")
                port = "/dev/"+s[0]
                baud = s[1]
                try:
                    ser = serial.Serial(port, baudrate=baud,  timeout=1)
                    serinit = True
                except:
                    serinit = False
        if serinit:
            data = ser.read(16)
            try:
                for msg in reader.next(data.decode("utf-8")):
                    parsednmea.put(msg) 
            except:
                pass
        else:
            parsednmea.put("ERROR")
            time.sleep(0.08)

##########################################
##########################################

tgui = Thread(target=GUI)
tnmea = Thread(target=NMEA)
tnmea.setDaemon(True)
tgui.start()
tnmea.start()
