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
rawserial = Queue(maxsize=0)

def GUI():
    screen = curses.initscr() 
    curses.noecho() 
    curses.curs_set(0) 
    screen.nodelay(1)
    curses.start_color()
    rawdata = False

    menu = [
        ['ttyUSB0', 'ttyUSB1', 'ttyUSB2'],
        ['4800', '9600', '19200', '38400'],
        ['parsed', 'raw']
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
    serialerror = False
    rawdatabuf = []

    class sentence:
        def __init__(self, msg, txt):
            self.msgtype = msg
            self.msg = txt
    def menucontrol(xmenu, ymenu, movement, serialport, baud, rawdata):

        if movement == "left":
            xmenu = xmenu-1
            xmenu = max(xmenu, 0)
            if xmenu == 0:
                ymenu = serialport
            elif xmenu == 1:
                ymenu = baud
            elif xmenu == 2:
                if rawdata:
                    ymenu = 1
                else:
                    ymenu = 0

        if movement == "down":
            ymenu = ymenu+1
            if xmenu == 0:                      
                ymenu = min(len(menu[0])-1, ymenu)
                serialport = ymenu
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif xmenu == 1:                    
                ymenu = min(len(menu[1])-1, ymenu)
                baud = ymenu
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif xmenu == 2:
                rawdata = True
                serialsettings.put("rawdata")
                if ymenu > 1:
                    ymenu = 1

        if movement == "up":
            ymenu = ymenu-1
            if xmenu == 0:                      
                ymenu = max(0, ymenu)
                serialport = ymenu
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif xmenu == 1:                    
                ymenu = max(0, ymenu)
                baud = ymenu
                serialsettings.put([menu[0][serialport]+","+menu[1][baud]])
            elif xmenu == 2:
                rawdata = False
                serialsettings.put("parsed")
                if ymenu < 0:
                    ymenu = 0

        if movement == "right":
            xmenu = xmenu+1
            xmenu = min(len(menu)-1, xmenu)
            if xmenu == 0:
                ymenu = serialport
            elif xmenu == 1:
                ymenu = baud
            elif xmenu == 2:
                if rawdata:
                    ymenu = 1
                else:
                    ymenu = 0


        return xmenu, ymenu, serialport, baud, rawdata

    while True: 
        screen.erase()
        #########Settings menu
        event = screen.getch() 
        if event == ord("q"): break 
        if event == ord("h"): menucursor[0], menucursor[1], serialport, baud, rawdata = menucontrol(menucursor[0], menucursor[1], "left", serialport, baud, rawdata)
        if event == ord("j"): menucursor[0], menucursor[1], serialport, baud, rawdata = menucontrol(menucursor[0], menucursor[1], "down", serialport, baud, rawdata)
        if event == ord("k"): menucursor[0], menucursor[1], serialport, baud, rawdata = menucontrol(menucursor[0], menucursor[1], "up", serialport, baud, rawdata)
        if event == ord("l"): menucursor[0], menucursor[1], serialport, baud, rawdata = menucontrol(menucursor[0], menucursor[1], "right", serialport, baud, rawdata)

        for l in range(len(menu)):
            for i in range(len(menu[l])):
                if menucursor == [l,i]:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(3))
                elif l == 0 and i == serialport: 
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                elif l == 1 and i == baud: 
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                elif l == 2 and i == 1 and rawdata:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                elif l == 2 and i == 0 and not rawdata:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(2))
                else:
                    screen.addstr((height-8)+i, 4+(l*12), menu[l][i], curses.color_pair(1))
        if serialerror:
            if int(time.time()) % 2 == 0:
                screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(4))
            else:
                screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(5))
        screen.refresh()
        ######data display
        if rawdata:
            while not rawserial.empty():
                rawstring = rawserial.get()
                rawdatabuf[0] += rawstring
                try:
                    screen.addstr(0, 0, str(rawdatabuf[0]))
                except:
                    pass
        else:
            found = False
            while not parsednmea.empty():
                msg = parsednmea.get()
                if msg == "ERROR":
                    serialerror = True
                elif msg == "OK":
                    serialerror = False
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
        time.sleep(0.05)

    curses.endwin()
    exit()

##serial handling
def NMEA():
    serinit = False
    reader = pynmea2.NMEAStreamReader()
    port = ""
    baud = 0
    rawmode = False
    while(True):
        while not serialsettings.empty():
            tset = serialsettings.get()
            if tset == "rawdata":
                rawmode = True
            elif tset == "parsed":
                rawmode = False
            else:
                for s in tset:
                    s = s.split(",")
                    port = "/dev/"+s[0]
                    baud = s[1]
                    try:
                        ser = serial.Serial(port, baudrate=baud,  timeout=1)
                        serinit = True
                        parsednmea.put("OK")
                    except:
                        serinit = False
                        parsednmea.put("ERROR")
        if serinit:
            data = ser.read(16)
            if rawmode:
                try:
                    rawserial.put(data)
                except:
                    pass
            else:
                try:
                    for msg in reader.next(data.decode("utf-8")):
                        parsednmea.put(msg) 
                except:
                    pass
        else:
            time.sleep(0.08)

##########################################
##########################################

tgui = Thread(target=GUI)
tnmea = Thread(target=NMEA)
tnmea.setDaemon(True)
tgui.start()
tnmea.start()
