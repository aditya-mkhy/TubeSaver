import time
from datetime import datetime
import os, sys
from pathlib import Path
import json
import socket
from random import choice

log = print

def print(*args):
    log(f"INFO [{datetime.now().strftime('%d-%m-%Y  %H:%M:%S')}] { ' '.join(args)}")


def resource_path(relative_path):
    path=os.path.dirname(sys.executable)    
    return path+'/'+relative_path

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def timeCal(sec):
    if sec < 60:
        return f"{int(sec)} Sec"
    elif sec < 3600:
        return f"{sec//60}:{ str(sec%60)[:2]} Mint"
    elif sec < 216000:
        return f"{sec//3600}:{ str(sec%3600)[:2]} Hrs"
    elif sec < 12960000:
        return f"{sec//216000}:{ str(sec%216000)[:2]} Days"
    else:
        return "CE"
    
def format_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size >= 900 and i < len(units) - 1:
        size /= 1024
        i += 1
    unit = units[i][:-1] if size == 1 else units[i]
    val = round(size, 2) if size < 10 else int(size)
    return f"{val} {unit}"


def is_online():
    try:
        s  = socket.socket()
        s.settimeout(0.5)
        s.connect(("pythonanywhere.com",443))
        s.close()
        return True
    except:
        return False
        
def genSessionId(len_ = 50, idList= []):
    data = "zxcvbnmasdfghjklqwertyuiop1234567890@ZXCVBNMASDFGHJKLQWERTYUIOP&&&&"
    id_ = ""
    for i in range(len_):
        id_ += choice(data)
    
    if id_ in idList:
        genSessionId(len_, idList)
    else:
        return id_

class DB(dict):
    def __init__(self):
        super().__init__()
        self.file = resource_path("data/db.tube")
        if os.path.exists(self.file):
            self.__read()
            return
        
        # if file not exits
        self.__write(refresh = True)

        
    def __read(self):
        with open(self.file, "r") as ff:
            try:
                self.update(json.loads(ff.read()))
            except:
                log("ErrorInDataBase: Can't read it..")
                return self.__write(refresh = True)
            
    
    def __write(self, refresh = False) -> dict:
        if refresh:
            self.__init_data()

        with open(self.file, "w") as tf:
            tf.write(json.dumps(self))

    def __init_data(self):
        self.update({
            "down" : []
        })
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__write()

    def commit(self):
        self.__write()
    

if __name__ == "__main__":
    print(format_size(1024 * 1024 * 200))