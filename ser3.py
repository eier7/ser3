#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

import curses 
import time
import pynmea2
import serial
import re
from queue import Queue
from threading import Thread

parsednmea = Queue(maxsize=0)
serialsettings= Queue(maxsize=0)

def GUI():
    screen = curses.initscr() 
    curses.noecho() 
    curses.curs_set(0) 
    screen.nodelay(1)
    curses.start_color()

    menu = [
        ['ttyUSB0', 'ttyUSB1', 'ttyUSB2'],
        ['4800', '9600', '19200', '38400'],
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

    class sentence:
        def __init__(self, msg, txt):
            self.msgtype = msg
            self.msg = txt
    def menucontrol(xmenu, ymenu, movement, serialport, baud):

        if movement == "left":
            xmenu = xmenu-1
            xmenu = max(xmenu, 0)
            if xmenu == 0:
                ymenu = serialport
            elif xmenu == 1:
                ymenu = baud

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

        if movement == "right":
            xmenu = xmenu+1
            xmenu = min(len(menu)-1, xmenu)
            if xmenu == 0:
                ymenu = serialport
            elif xmenu == 1:
                ymenu = baud


        return xmenu, ymenu, serialport, baud

    while True: 
        screen.erase()
        #########Settings menu
        event = screen.getch() 
        if event == ord("q"): break 
        if event == ord("h"): menucursor[0], menucursor[1], serialport, baud = menucontrol(menucursor[0], menucursor[1], "left", serialport, baud)
        if event == ord("j"): menucursor[0], menucursor[1], serialport, baud = menucontrol(menucursor[0], menucursor[1], "down", serialport, baud)
        if event == ord("k"): menucursor[0], menucursor[1], serialport, baud = menucontrol(menucursor[0], menucursor[1], "up", serialport, baud)
        if event == ord("l"): menucursor[0], menucursor[1], serialport, baud = menucontrol(menucursor[0], menucursor[1], "right", serialport, baud)

        for m in range(len(menu)):
            if menucursor[0] == 0: 
                screen.addstr(height-1, 20, menu[0][serialport], curses.color_pair(2))
                screen.addstr(height-1, 30, menu[1][baud], curses.color_pair(1))
            elif menucursor[0] == 1:
                screen.addstr(height-1, 20, menu[0][serialport], curses.color_pair(1))
                screen.addstr(height-1, 30, menu[1][baud], curses.color_pair(2))
        if serialerror:
            if int(time.time()) % 2 == 0:
                screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(4))
            else:
                screen.addstr(height-1, 0, "SERIAL PORT ERROR", curses.color_pair(5))
        screen.refresh()
        ######data display
        while not parsednmea.empty():
            found = False
            msg = parsednmea.get()
            if msg == "ERROR":
                serialerror = True
            elif msg == "OK":
                serialerror = False
            else:
                try:
                    msgtype = re.match("\$..(\w*),", msg).group(1)
                except:
                    msgtype = "err"
                for item in sentences:
                    if item.msgtype ==  msgtype:
                        item.msg = msg
                        found = True
                if not found and msgtype != 'err':
                    sentences.append(sentence(msgtype, msg))
        for s in range(min(len(sentences), 7)):
            screen.addstr(s, 0, str(sentences[s].msg).replace("\n", ""))

        screen.refresh()
        time.sleep(0.05)

    curses.endwin()
    exit()

##serial handling
def NMEA():
    serinit = False
    port = ""
    baud = 0
    while(True):
        while not serialsettings.empty():
            tset = serialsettings.get()
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
            data = ser.readline().decode("utf-8", "ignore")
            parsednmea.put(data) 
        else:
            time.sleep(0.08)

##########################################
##########################################

tgui = Thread(target=GUI)
tnmea = Thread(target=NMEA)
tnmea.setDaemon(True)
tgui.start()
tnmea.start()
