import time
from datetime import datetime
import os, sys
from pathlib import Path

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
    st=None
    if size < 1024:
        st=f'{size} Bytes'
        
    elif size < 1022976 :
        size=str(size/1024).split('.')
        size=size[0]+'.'+(size[1])[:1]
        st=f'{size} KB'

    elif size < 1048576 :
        size=str(size/1048576).split('.')
        size=size[0]+'.'+(size[1])[:2]
        st=f'{size} MB'

    elif size < 1047527424:
        
        size=str(size/1048576).split('.')
        size=size[0]+'.'+(size[1])[:1]
        st=f'{size} MB'
        
    elif size < 1073741824:
        
        size=str(size/1073741824).split('.')
        size=size[0]+'.'+(size[1])[:2]
        st=f'{size} GB'
        
    elif size >= 1073741824:
        size=str(size/1073741824).split('.')
        size=size[0]+'.'+(size[1])[:1]
        st=f'{size} GB'
    else:
        st='Error_in_cal'
    return st


if __name__ == "__main__":
    print(format_size(1024 * 1024 * 200))