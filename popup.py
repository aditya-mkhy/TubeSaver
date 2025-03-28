import win32gui
import win32con
import win32ui
import win32api
from tkinter import messagebox


from win32com.shell import shell, shellcon  # pycharm cannot find those import but it will be interpreted

from tkinter import *
from PIL import Image, ImageTk
from webbrowser import open as open_file
import os, sys
from time import sleep
import ctypes
from threading import Thread, Timer
from tkinter.filedialog import   askdirectory 
from extra import resource_path, print
from functools import partial as functools_partial
import subprocess

from PIL import Image, ImageTk

from tkinter.ttk import Style as ttk_Style,Progressbar,Scale as ttk_Scale

ctypes.windll.shcore.SetProcessDpiAwareness(1)


def get_icon(PATH):
    #get icon of a file extention
    SHGFI_ICON = 0x000000100
    SHGFI_ICONLOCATION = 0x000001000
    SHGFI_USEFILEATTRIBUTES = 0x000000010
    SHIL_SIZE = 0x00002

    ret, info = shell.SHGetFileInfo(PATH, 0, SHGFI_ICONLOCATION | SHGFI_ICON | SHIL_SIZE | SHGFI_USEFILEATTRIBUTES)
    hIcon, iIcon, dwAttr, name, typeName = info
    ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
    hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    hbmp = win32ui.CreateBitmap()
    hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
    hdc = hdc.CreateCompatibleDC()
    hdc.SelectObject(hbmp)
    hdc.DrawIcon((0, 0), hIcon)
    win32gui.DestroyIcon(hIcon)

    bmpinfo = hbmp.GetInfo()
    bmpstr = hbmp.GetBitmapBits(True)

    img = Image.frombuffer(
        "RGBA",
        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
        bmpstr, "raw", "BGRA", 0, 1
    )


    return img

def custom_shape_canvas(parent : Canvas = None, width=300, height=100, rad=50, padding=3, bg='red'):
    color=bg
    cornerradius=rad
    rad = 2*cornerradius
    parent.create_polygon((padding,height-cornerradius-padding,padding,cornerradius+padding,
                           padding+cornerradius,padding,width-padding-cornerradius,padding,
                           width-padding,cornerradius+padding,width-padding,height-cornerradius-padding,
                           width-padding-cornerradius,height-padding,padding+cornerradius,height-padding),
                          fill=color, outline=color)

    parent.create_arc((padding,padding+rad,padding+rad,padding), start=90, extent=90, fill=color,
                      outline=color)
    parent.create_arc((width-padding-rad,padding,width-padding,padding+rad), start=0, extent=90,
                      fill=color, outline=color)
    parent.create_arc((width-padding,height-rad-padding,width-padding-rad,height-padding), start=270,
                      extent=90, fill=color, outline=color)
    parent.create_arc((padding,height-padding-rad,padding+rad,height-padding), start=180, extent=90,
                      fill=color, outline=color)

class AnimeleButton(Button):
    def __load__(self, path):
        self.pauseSt = False
        img = Image.open(path)
        self.indx = 0
        self.frames = []

        for i in range(img.n_frames):
            self.frames.append(ImageTk.PhotoImage(img.copy()))
            img.seek(i)

        try:
            self.delay = img.info['duration']
            self.delayDefault = img.info['duration']
        except:
            self.delay = 100



    def next_frame(self):
        self.indx += 1
        self.indx %= len(self.frames)

        if not self.pauseSt:
            self.config(image=self.frames[self.indx])
            self.after(self.delay, self.next_frame)

    def play(self, event=None):
        self.pauseSt = False
        self.next_frame()

    def stop(self, event=None):
        self.pauseSt = True
        self.config(image=self.frames[0])



class AnimeleLabel(Label):
    def __load__(self, path):
        self.pauseSt = False
        img = Image.open(path)
        self.indx = 0
        self.frames = []

        for i in range(img.n_frames):
            self.frames.append(ImageTk.PhotoImage(img.copy()))
            img.seek(i)

        try:
            self.delay = img.info['duration']
            self.delayDefault = img.info['duration']
        except:
            self.delay = 100



    def next_frame(self):
        self.indx += 1
        self.indx %= len(self.frames)

        if not self.pauseSt:
            self.config(image=self.frames[self.indx])
            self.after(self.delay, self.next_frame)

    def play(self, event=None):
        self.pauseSt = False
        self.next_frame()

    def stop(self, event=None):
        self.pauseSt = True
        self.config(image=self.frames[0])




class  popWind:
    def __init__(self, width, height, bg, align="left"):
        self.width = width
        self.height = height
        self.bg = bg
        self.align = align

        self.win = Toplevel()
        self.win.withdraw()
        self.win.config(bg="red")

        self.win.overrideredirect(True)
        self.win.tk.call('tk', 'scaling', 1)
        self.win.wm_attributes('-transparentcolor', 'red')


        self.frame = Canvas(self.win,bg='red',bd=0,  width=self.width, height=self.height, highlightthickness=0)  
        self.frame.pack(fill='both',expand=True, padx=1, pady=1)

        custom_shape_canvas(parent=self.frame, width=self.width, height=self.height, rad=12, padding=0, bg=self.bg)
        self.win.bind("<FocusOut>" , self.hide)


    def hide(self, event=None):
        self.win.withdraw()

    def pop(self, x, y):
        if self.align == "left":
            x = (x - self.width)+ 5
        self.win.geometry(f"+{x}+{y}")
        self.win.deiconify()
        self.win.focus_force()

    def destroy(self, event=None):
        self.win.destroy()
        exit()


class DownloadsInfoWin(popWind):
    def __init__(self, width, height, clear_but_cmd = None):
        
        self.bg = "#252323"
        self.bdbg = "grey35"
        self.container_bg = "grey15"
        self.__min_height__ = 135
        self.clear_but_cmd = clear_but_cmd


        # popWin class Initialization...........
        super().__init__(width, height, self.bg)

        #ProgressBar  Style config...
        self.style_Scale = ttk_Style(self.win)
        self.style_Scale.theme_use('alt')
        self.style_Scale.configure("black.Horizontal.TProgressbar", background='royalblue', thickness=5)

        self.title = Label(self.frame, text="Downloads", bg=self.bg, fg="grey96", font=("Halvatica", 32, "bold"), bd=0)
        self.title.place(x=16, y=14)

        self.bord = Frame(self.frame, bg=self.bdbg, width=width-30, height=1)
        self.bord.place(x=15, y=60)

        #Folder icon
        self.folder_img = Image.open(resource_path("data/open.png"))
        self.folder_icon = ImageTk.PhotoImage(self.folder_img.copy())
        self.folder_icon_small = ImageTk.PhotoImage(self.folder_img.resize((37, 37), Image.LANCZOS).copy())# small icon for enter event


        #Scroll Windows....
        self.scrollWinCanvas = Canvas(self.frame, bg=self.bg, bd=0, closeenough=0, highlightthickness=0, confine=1,
                                    width=width, height=height-136)
        self.scrollWinCanvas.place(x=0, y=61)
                               
        self.scrollFrame =Frame(self.scrollWinCanvas, bg=self.bg)

        self.scrollFrame.bind("<Configure>",lambda e: self.scrollWinCanvas.configure(scrollregion=self.scrollWinCanvas.bbox("all")))
        self.scrollWinCanvas.create_window((0, 0), window=self.scrollFrame, anchor="nw")

        self.scrollWinCanvas.bind("<MouseWheel>", lambda event : self.scroll(event))


        #Clear Button
        self.clear_img = ImageTk.PhotoImage(file=resource_path("data/but.png"))
        self.clear_img_hover = ImageTk.PhotoImage(file=resource_path("data/but2.png"))

        self.clear_but = Button(self.frame, highlightbackground=self.bg, image=self.clear_img, relief="flat",
                        bd=0, compound='right', activebackground=self.bg, cursor='hand2', bg=self.bg,
                        command=self.clear_cmd)
        self.clear_but.place(x=80, y=height-60)

        self.clear_but.bind("<Enter>", lambda evt : self.clear_but.config(image=self.clear_img_hover))
        self.clear_but.bind("<Leave>", lambda evt : self.clear_but.config(image=self.clear_img))


        #Button2__
        
        self.cancel_but = Button(self.frame, highlightbackground=self.bg, image=self.clear_img, relief="flat",
                        bd=0, compound='right', activebackground=self.bg, cursor='hand2', bg=self.bg,
                        command=self.hide)
        self.cancel_but.place(x=(width)-203, y=height-60)

        self.cancel_but.bind("<Enter>", self.cancel_but_label_enter)
        self.cancel_but.bind("<Leave>", self.cancel_but_label_leave)

        self.cancel_but_label = Label(self.frame, text="Cancel", bd=0,compound='right', cursor='hand2', bg="#212020", fg="white",
                                    font=('yu gothic ui', 20), width=8, justify="center")
        self.cancel_but_label.place(x=(width)-194, y=height-52)
        self.cancel_but_label.bind("<Enter>", self.cancel_but_label_enter)
        self.cancel_but_label.bind("<Leave>", self.cancel_but_label_leave)

        self.cancel_but_label.bind("<Button-1>", self.single_click_on_cancel_but_label)
        self.cancel_but_label.bind("<ButtonRelease-1>", self.single_relese_click_on_cancel_but_label)


        self.bord = Frame(self.frame, bg=self.bdbg, width=width-30, height=1)
        self.bord.place(x=15, y=height-75)

        #Def
        self.ext_icons = {} #Dict of icons of different icons
        self._dont_save_ext = [".lnk", ".exe"] #List of extentions which should'nt be saved.
        self.no_of_prog = 0
        self.prev_single_click_obj = None

    def move_to(self, val):
        self.scrollWinCanvas.yview_moveto(val)

    def clear_history(self):
        if self.clear_but_cmd != None:
            r = self.clear_but_cmd()
            print(f"R===> {r}")
            if r:
                print("Hostory is deleted ")
                for child in self.scrollFrame.winfo_children():
                    child.destroy()


    def single_relese_click_on_cancel_but_label(self, event):
        self.cancel_but.event_generate("<ButtonRelease-1>")
        self.hide()


    def single_click_on_cancel_but_label(self, event):
        self.cancel_but.event_generate("<Button-1>")

    def cancel_but_label_enter(self, event):
        self.cancel_but.config(image=self.clear_img_hover)
        self.cancel_but_label.config(bg="#3B3A3A")


    def cancel_but_label_leave(self, event):
        self.cancel_but.config(image=self.clear_img)
        self.cancel_but_label.config(bg="#212020")


    def increase_height_on_add(self):
        self.no_of_prog += 1

        if self.no_of_prog < 7:
            height = self.__min_height__ + (self.no_of_prog*85)
            self.scrollWinCanvas.config(height=height-135)


    def scroll(self, event):
        self.scrollWinCanvas.yview("scroll",-1*int(event.delta/120),"units")

    def clear_cmd(self):
        self.win.unbind("<FocusOut>")
        rslt = messagebox.askokcancel("Clear Message", f"     Are you sure you want to delete Downloads History.", parent=self.win)
        self.win.bind("<FocusOut>" , self.destroy)
        if rslt:
            print("deleting....hist")
            self.clear_history()

        


    def add_prog(self, path):
        return AddProgItem(self, path)


class AddProgItem():
    def __init__(self, parent, path: str):
        self.parent = parent
        self.path = path
        _ , self.ext = os.path.splitext(self.path) # File Extention

        #Defalult Value.....
        timeSt = "Download Complete" 
        downSt = ""

        self.pause_cmd = None

        self.is_completed = False

        #increase height on file add
        self.parent.increase_height_on_add()


        self.container = Frame(self.parent.scrollFrame, bg=self.parent.container_bg, width=self.parent.width, height=85)# container to contain objets
        self.container.pack(side="bottom", expand=True, fill="x")
        self.container.bind("<Leave>", self.container_leave_event)
        self.container.bind("<Enter>", self.container_enter_event)


        #Icon label to palce icon
        self.icon_label = Label(self.container,
                        bd=0,compound='right', cursor='hand2', bg=self.parent.container_bg)
        self.icon_label.place(x=20, y=20)
        self.icon_label.bind("<Enter>", self.icon_enter_event)
        self.icon_label.bind("<Leave>",  self.icon_leave_event)
        self.icon_label.bind("<Double-1>", self.open_file_on_click) # open file on double click

        #Add extention icon
        self.extention_handler(self.ext)

        # File name label
        self.file_name = Label(self.container, text=self.short_file_name(), fg='white', bg=self.parent.container_bg, font=('yu gothic ui', 20, "bold"), 
                            anchor="w", width=38, bd=0, justify="left", cursor="hand2")
        self.file_name.place(x=82, y=8)
        self.file_name.bind("<Enter>", self.file_name_enter_event)
        self.file_name.bind("<Leave>", self.file_name_leave_event)
        self.file_name.bind("<Double-1>", self.open_file_on_click) # open file on double click


        #Progress_bar to display progress
        self.progress_bar = Progressbar(self.container, length=455, style="black.Horizontal.TProgressbar",
                        maximum=100, value=0, mode="determinate", orient="horizontal")            
        self.progress_bar['value'] = 60
        self.progress_bar.place(x=84, y=42)


        self.time_left=Label(self.container, text=timeSt, bg=self.parent.container_bg, fg='grey80',font=('',17), anchor="w", justify="left")
        self.time_left.place(x=82,y=52)

        # down_status to show the speed of download
        self.down_status=Label(self.container, text=downSt, bg=self.parent.container_bg, fg='grey90', 
                                font=('',17), anchor="e", width=33, justify="right")
        self.down_status.place(x=236,y=52)

        #open_folder button to select the file in file explorer....
        self.open_folder = Button(self.container, highlightbackground=self.parent.bg, image=self.parent.folder_icon,
                        bd=0, compound='right', activebackground='grey20',cursor='hand2', bg=self.parent.container_bg,
                        command=self.open_file_in_explorer)
        self.open_folder.place(x=self.parent.width-60, y=20)
        self.open_folder.bind("<Enter>", self.open_folder_enter_event)
        self.open_folder.bind("<Leave>", self.open_folder_leave_event)


        #Binding scroll event....
        self.container.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.icon_label.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.file_name.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.progress_bar.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.time_left.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.down_status.bind("<MouseWheel>", lambda event : self.parent.scroll(event))
        self.open_folder.bind("<MouseWheel>", lambda event : self.parent.scroll(event))

        # single click
        self.container.bind("<Button-1>", self.container_single_click_event)
        # self.icon_label.bind("<Button-1>", self.container_single_click_event)
        self.file_name.bind("<Button-1>", self.container_single_click_event)
        self.progress_bar.bind("<Button-1>", self.container_single_click_event)
        self.time_left.bind("<Button-1>", self.container_single_click_event)
        self.down_status.bind("<Button-1>", self.container_single_click_event)


        
        #border......
        self.bord = Frame(self.container, bg=self.parent.bdbg, width=self.parent.width-30, height=1)
        self.bord.place(x=15, y=84)

    def extention_handler(self, ext=None):
        #get icon of a file extention
        if ext in self.parent.ext_icons:
            # reuse of saved icon
            self.icon = self.parent.ext_icons[ext]
            self.icon_small = self.parent.ext_icons[f"{ext}_small"]
        
        else:
            img = get_icon(self.path)
            self.icon = ImageTk.PhotoImage(img.copy()) #icon 
            self.icon_small = ImageTk.PhotoImage(img.resize((40, 40), Image.LANCZOS).copy()) # small icon for cursor enter event

            # saving icons for reuse
            if ext not in self.parent._dont_save_ext:
                self.parent.ext_icons[ext] = self.icon
                self.parent.ext_icons[f"{ext}_small"] = self.icon_small
        
        self.icon_label.config(image=self.icon)

    
    def config(self, path=None, max_size=None, pause_cmd=None, state=None, ext=None):
        if path:
            self.path = path
        if state:
            if state == "complete":
                self.download_complete()
        if max_size:
            self.progress_bar.config(maximum=max_size)

        if pause_cmd:
            self.pause_cmd

        if ext:
            if ext != self.ext:
                self.extention_handler(ext)


    def update(self, value=None, timest=None, speed=None):
        if value:
            self.progress_bar['value'] = value
        if timest:
            self.time_left.config(text=timest)
        if speed:
            self.down_status.config(text=speed)





    def container_single_click_event(self, event=None):
        if self.parent.prev_single_click_obj:
            self.parent.prev_single_click_obj.container_leave_event(event="ch")

        self.container_enter_event(col="#254454")
        self.parent.prev_single_click_obj = self


    def download_complete(self):
        self.is_completed = True
        self.file_name.config(font=('yu gothic ui', 21, "bold"))
        self.file_name.place_configure(x=82, y=12)
        self.time_left.place_configure(x=82, y=46)
        self.progress_bar.destroy()
        self.down_status.destroy()
        

    def short_file_name(self) -> str:
        basename = os.path.basename(self.path)
        l = 42
        if len(basename) > l:
            name = f"{basename[:l-len(self.ext)]}..{basename[len(basename) -len(self.ext):]}"
        else:
            name = basename
        return name

    def file_name_enter_event(self, event):
        self.file_name.config(fg="grey80")

    def file_name_leave_event(self, event):
        self.file_name.config(fg="white")

    def icon_leave_event(self, event=None):
        self.icon_label.config(image=self.icon)

    def icon_enter_event(self, event=None):
        self.icon_label.config(image=self.icon_small)

    def open_folder_leave_event(self, event=None):
        self.open_folder.config(image=self.parent.folder_icon)

    def open_folder_enter_event(self, event=None):
        self.open_folder.config(image=self.parent.folder_icon_small)
        
    def open_file_on_click(self, event=None):
        self.container_enter_event(col="#6f5923", event="ch")
        txt = self.time_left.cget("text")
        self.time_left.config(text="Opening file")

        self.parent.win.update()
        open_file(self.path)
        sleep(0.1)
        self.time_left.config(text=txt)


    def open_file_in_explorer(self):
        self.container_enter_event(col="#6f5923", event="ch")
        txt = self.time_left.cget("text")
        self.time_left.config(text="Opening in explorer")

        self.parent.win.update()
        path=self.path.replace('/','\\')
        subprocess.run(f'explorer /select, "{path}"')        
        sleep(0.1)
        self.time_left.config(text=txt)


    def container_leave_event(self, event=None, col=None):
        if self.container.cget("bg") == "#254454" and event != "ch":
            return 0
        
        if not col:
            col = self.parent.bg
            
        self.container.config(bg=col)
        self.file_name.config(bg=col)
        self.icon_label.config(bg=col)
        self.time_left.config(bg=col)
        try:
            self.open_folder.config(bg=col)
        except:
            pass
        if not self.is_completed:
            self.down_status.config(bg=col)


    def container_enter_event(self, event=None, col=None):
        if self.container.cget("bg") == "#254454" and event != "ch":
            return 0
        
        if not col:
            col = "grey20"

        self.container.config(bg=col)
        self.file_name.config(bg=col)
        self.icon_label.config(bg=col)
        self.time_left.config(bg=col)
        try:
            self.open_folder.config(bg=col)
        except:
            pass
        if not self.is_completed:
            self.down_status.config(bg=col)

        

class LoadPopUp(popWind):
    def __init__(self, path=None, parent=None):
        if path:
            self.gifPath = path
        else:
            raise ValueError("File Name")
        
        self.parent = parent
        self.width = 450
        self.height = 450
        self.bg = "black"
        self.hidden_col = "#010000"
        self.stop_val = False
        self.pause = False
        self.indx = 0

        self.frames = []

        self.delay = 50
        self.delayDefault = self.delay

        self.win = Toplevel(self.parent)
        self.win.config(bg=self.hidden_col)
        self.win.overrideredirect(True)

        self.win.geometry(f"{self.width}x{self.height}")
        self.win.withdraw()


        self.win.tk.call('tk', 'scaling', 1)

        self.win.wm_attributes('-transparentcolor', self.hidden_col)
        self.win.attributes("-topmost", True)

        self.prog = Label(self.win, bd=0, relief="flat", compound="left", anchor="nw", bg=self.hidden_col)
        self.prog.pack(side="top", fill="both", expand=True)
        Thread(target=self.__load__).start()

        # self.win.bind("<FocusOut>" , self.destroy)
        # self.win.focus_force()
        # self.win.mainloop()
    
    def __load__(self):
        img = Image.open(self.gifPath)
        
        for i in range(img.n_frames):
            self.frames.append(ImageTk.PhotoImage(img.copy()))
            img.seek(i)

    def set_dely(self, val):
        self.delay = val

    def show(self, x, y):
        self.stop_val = False
        self.win.geometry(f"+{x}+{y}")
        self.win.deiconify()
        self.win.focus_force()
        Thread(target=self.next_frame, daemon=True).start()


    def stop(self):
        self.stop_val = True
        self.hide()

    def next_frame(self):
        l = len(self.frames)
        if  l > 0:
            self.indx += 1
            self.indx %= l

            if not self.stop_val:
                Timer((self.delay/1000), self.next_frame).start()
                self.prog.config(image=self.frames[self.indx])
                self.win.update()
                # self.prog.after(self.delay, self.next_frame)


    def hide(self):
        self.win.withdraw()


    def destroy(self, event=None):
        self.win.destroy()
        exit()




if __name__ == "__main__":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)


    root = Tk()
    l = LoadPopUp()
    l.show()

   