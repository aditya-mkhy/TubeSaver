from extra import resource_path, timeCal, format_size
import os ,sys,subprocess
from tkinter import messagebox


# path = resource_path("vcruntime140_1.dll")

# if not  os.path.exists(path):
#     dll = resource_path("d11.txt")
#     dll2 = resource_path("d22.txt")

#     ch_dll = resource_path("vcruntime140.dll")
#     ch_dll2 = resource_path("vcruntime140_1.dll")

#     os.rename(dll, ch_dll)
#     os.rename(dll2, ch_dll2)


from tkinter import *
from tkinter import messagebox
from json import loads, dump
from requests import get as requests_get
import os , sys, subprocess
from random import choice
from PIL import ImageTk, Image, ImageOps, ImageDraw
from random import randint
import ctypes
from youtubesearchpython import VideosSearch , ResultMode #pip install youtube-search-python
from functools import partial as functools_partial
from pathlib import Path
from tkinter.ttk import Style as ttk_Style,Progressbar, Scale as ttk_Scale

from webbrowser import open as open_file

from mutagen.mp3 import MP3
from mutagen.id3 import ID3,TIT2,TLEN,TCON,TPE1,TALB,TDES,TPUB,WPUB,TDRL,APIC
import io as io_import
from cryptography.fernet import Fernet
from threading import Thread, Timer
from time import time, sleep, ctime
from popup import DownloadsInfoWin, LoadPopUp, AnimeleButton, AnimeleLabel
from login import LoginPage, genSessionId

from utube import get_video_info, Dtube, get_thumbnail
from tkinter import font

##youtube_dl\downloader\common.py  nopart  == True


class YouTube_Download():

    def __init__(self,parent_window: Tk, loginwindow, root):
        self.width = 1200
        self.height = 800
        self.loginwindow = loginwindow
        self.parent=parent_window
        self.root = root
        self.video_image_list=[]
        self.video_id=None
        self.stop_serch_value =False
        self.stop_config_result = False
        self.entry_var=StringVar()
        self.functools_partial=functools_partial
        self.video=None
        self.show_down_status_frame=False
        self.version = "9.0.0"
        self.thumbnails = {}
        self.thumbnails_icon = {}
        self.infoFrameForUpdate = []
        self.numHistory = 10
        self.popUpWin = DownloadsInfoWin(width=630, height=645, clear_but_cmd=self.clear_download_history)

        #___window
        self.label=Frame(self.parent, bg='grey20')
        self.label.pack(side='top',fill='x')

        self.entry_wgt=Entry(self.label, textvariable=self.entry_var, fg='#0065ff', bg='grey17', font=("yu gothic ui", 24, 'bold'),
                        bd=2, relief='sunken', insertbackground='grey70')
        self.entry_wgt.pack(side='left',fill='x',padx=6,expand=True,pady=6, ipadx=1, ipady=1)
        
        self.entry_var.set('Search')

        self.entry_wgt.bind('<Return>',self.search_entry)
        self.entry_wgt.bind("<FocusIn>",self.focus_in_entry_widget)
        self.entry_wgt.bind("<FocusOut>",self.focus_out_entry_widget)


        self.download_image=PhotoImage(file=resource_path('data/download.png'),master=self.parent)

        self.download_butn=AnimeleButton(self.label, bg='grey20', bd=0,
                                  highlightbackground='grey20', activebackground='grey20',
                                  command=self.show_pop_win, cursor="hand2")
        self.download_butn.pack(side='left',padx=30)


        self.download_butn.__load__(resource_path("data/download.gif"))
        self.download_butn.stop()
        self.download_butn.bind("<Enter>", lambda e: self.start_down_animation(None))
        self.download_butn.bind("<Leave>", lambda e: self.stop_down_animation(None))

        self.back = "#0f0f0f"

 
        self.canvas =Canvas(self.root, bg=self.back, bd=0, closeenough=0, highlightthickness=0, confine=1)
        self.canvas.pack(side="top", fill="both", expand=True, anchor="nw")
        

        self.scrollable_frame =Frame(self.canvas, bg=self.back, pady=8)
        self.parent.bind("<Configure>", self.configAll)



        self.scrollable_frame.bind("<Configure>",lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))


        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
                
        self.style_Scale = ttk_Style(self.parent)
        self.style_Scale.theme_use('alt')
        self.style_Scale.configure("black.Horizontal.TProgressbar", background='royalblue',thickness=4)
        self.parent.bind_all("<Control-Shift-r>",self.close_ffmpeg )
        self.parent.bind_all("<Control-Shift-R>",self.close_ffmpeg )
        self.pause_img=PhotoImage(file=resource_path('data/download_pause.png'),master=self.parent)
        self.resume_img=PhotoImage(file=resource_path('data/download_resume.png'),master=self.parent)
        self.folder_img=PhotoImage(file=resource_path('data/folder.png'),master=self.parent)
        self.folder_img=self.folder_img.subsample(3,3)


        #____Top_Level
        self.root_width_saved=0
        self.imagesData = {}
        self.prevIdd = []

        self.max_pixl = 240
        self.my_font = font.Font(family="yu gothic ui", size=20, weight="bold")

        # for load gif
        gif_path = resource_path("data/load.gif")
        self.load_prog = LoadPopUp(gif_path, self.parent)
        self.load_prog.set_dely(20)
        Thread(target=self.on_start_search, daemon=True).start()

        self.down_process_list = []
        self.no_internet_animation_is_active = False



 
    def start_down_animation(self, idd=None):
        print(f"idd==> {idd}")
        if self.down_process_list == []:
            self.download_butn.play()
            print("Animation starts")
        else:
            print("Animations is already running....")

        if idd:
            print("Procee is added")
            self.down_process_list.append(idd)
        else:
            print("This is a enter event")

    def stop_down_animation(self, idd=None):
        print(f"idd==> {idd}")
        if idd:
            self.down_process_list.remove(idd)
            print(f"Idd is revoved==> {idd}")
        else:
            print(f"This is a leave event....")

        if self.down_process_list == []:
            self.download_butn.stop()
            print(f"Stoping the animation==> {self.down_process_list}")
        else:
            print(f"other proceess exits==> {self.down_process_list}")

    def clear_download_history(self):
        try:
            alldata = self.loginwindow.getData()
            alldata["downloads"] = []
            self.loginwindow.writeData(alldata)
            return True
        except:
            return False
        
    def no_internet_animation(self):
        self.no_con_anime_path = resource_path("data/offline.gif")
        self.no_connection_anime = AnimeleLabel(self.scrollable_frame, bd=0, bg=self.back, compound="center")
        self.no_connection_anime.__load__(self.no_con_anime_path)
        self.no_connection_anime.play()
        self.no_internet_animation_is_active = True
        self.no_connection_anime.pack(side="top", fill="both", expand=True, padx=280, pady=50)
        
    def config_internet_animation(self):
        if self.no_internet_animation_is_active:
            x = (self.root.winfo_width()//2) -300
            y = (self.root.winfo_height() //2) -360
            try:
                self.no_connection_anime.pack_configure(padx=x, pady=y)
            except:
                pass



    def on_start_search(self):
        self.search("Songs")
        self.history()



    def focus_in_entry_widget(self,event):
        self.entry_wgt.config(fg='#0065ff', font=("yu gothic ui", 24, 'bold'),)
        d=self.entry_var.get()
        if d =='Search' or d =='YouTube':
            self.entry_var.set('')
      
    def focus_out_entry_widget(self,event):
        d=self.entry_var.get()
        if d.strip() == '':
            self.entry_var.set('Search')
            self.entry_wgt.config(fg='#0065ff', font=("yu gothic ui", 24, 'bold'),)

           
    def dwn_scroll_window(self,event):
        self.dwn_canvas.yview("scroll",-1*int(event.delta/120),"units")

    def DownloadPlaylist(self, video_name):
        video_name=video_name.split("---")
        video_id =video_name[0]
        print("DownlaodingPlayList===> ",video_id)
        try:
            quality=video_name[1]
            if quality == "none":
                quality = None

        except:
            quality=None
        try:
            downList=loads(video_name[2])
            print("DownloadList====>",downList
            )
        except:
            downList=[]
        print("video_id==>",video_id)
        print("quality==>",quality)
        print("downList==>",downList)
        try:
            Plist=Playlist(video_id)
        except Exception as e:
            if not self.loginwindow.isOnline():
                messagebox.showinfo("YouTube", "     Computer not connected. Make sure your computer has an\n     active Internet Connection")
            else:
                messagebox.showerror("YouTube Error 33", f"     {e}")
            return 0
        
        notInc = '<>:"/\\|?*'+"'"
        try:
            dirname = ""
            for w in Plist.title:
                if w not in notInc:
                    dirname+=w
            dirname+="/"
        except:
            dirname = ""

        ddir=str(Path.home())+f'\\Videos/{dirname}'
        if not os.path.exists(ddir):
            try:
                os.mkdir(ddir)
            except:
                print("Error in creating direcory... ")
                ddir=str(Path.home())+f'\\Videos/'

        print("Total Viodes ==> ",len(Plist.video_urls))

        count=0
        for urls in Plist.video_urls:
            print("Urls======> ",urls)
            count+=1
            if count in downList or downList == []:
                self.video = YouTube(urls)#, use_oauth=True, allow_oauth_cache=True)
                itag=None

                if quality==None:
                    vstream=self.video.streams.filter(progressive=True , file_extension='mp4')
                    l = len(vstream)
                    if l > 0:
                        itag = vstream[l-1].itag
                    else:
                        vstream=self.video.streams.filter(adaptive=True, only_video=True, file_extension='mp4')[0]
                        itag=vstream.itag

                elif quality=="high":
                    vstream=self.video.streams.filter(adaptive=True, only_video=True, file_extension='mp4')[0]
                    print("vstream ==> ", vstream)
                    itag=vstream.itag
                else:
                    for vstream in self.video.streams.filter(adaptive=True,only_video=True,file_extension='mp4'):
                        if quality in vstream.resolution:
                            itag=vstream.itag
                            print("Desired resolution fouund")
                             
                        else:
                            print("Desired Vidoe Resolution is Not Found \n Downloading Highest quality")
                            vstream=self.video.streams.filter(adaptive=True,only_video=True,file_extension='mp4')[0]
                            itag=vstream.itag

                if itag != None:
                    video_stream=self.video
                    widget=None
                    try:
                        print("Downloading_Video==>",vstream.default_filename)
                    except Exception as e:
                        print("Error[990]",e)
                    self.try_download_selected_video(itag,video_stream,widget, ddir)
            print("\n-------------------------------------------------------\n")
        
    def search_entry(self, event=None):
        video_name=self.entry_var.get()
        if "www.youtube.com/playlist?" in  video_name:
            t=Thread(target=self.DownloadPlaylist,args=(video_name,) , daemon=True)
            t.start()
            #url|||resulution|||[1,2,3]
        elif "www.youtube.com/watch?v=" in video_name:
            print("Video link found... Downloding....")
            t = Thread(target=self.call_download_menu, args=(event, None, video_name))
            t.start()
            
        else:
            self.search(video_name)

    def show_load_pop(self):
        print("Showing...")
        x = self.root.winfo_x() + (self.root.winfo_width()//2) -200
        y = self.root.winfo_y() + (self.root.winfo_height()//2) -200
        self.load_prog.show(x, y)
        

    def show_pop_win(self, st=None):

        x = self.root.winfo_x()
        y = self.root.winfo_y()

        x1 = self.download_butn.winfo_x() + self.download_butn.winfo_width()+20
        y1 = self.download_butn.winfo_y() + self.download_butn.winfo_height()+55

        self.popUpWin.pop(x+x1, y+y1)             


    def search(self, video_name):
        try:
            self.video_image_list=[]
            self.stop_config_result = randint(100, 10000000)
            
            self.entry_wgt.unbind('<Return>')
            self.entry_wgt.config(insertontime=0)
            self.search_result_youtube = VideosSearch(video_name, region="IN")
            self.no_internet_animation_is_active = False
            try:
                self.clear_win()
            except Exception as e:
                print(f"Error--incleaning==={e}")
            
            th=Thread(target=self.configure_search_result, args=(self.stop_config_result,), daemon = True)
            th.start()
            
        except Exception as e:
            if not self.loginwindow.isOnline():
                if not self.no_internet_animation_is_active:
                    self.no_internet_animation()
                messagebox.showinfo("YouTube", "     Computer not connected. Make sure your computer has an\n     active Internet Connection")
            else:
                messagebox.showerror("YouTube Error 44", f"     {e}")

        finally:
            self.entry_wgt.config(insertontime=300)
            self.entry_wgt.bind('<Return>',self.search_entry)

    def addHistory(self, file: str):
        # print(f"File=========> {file}")
        prog = self.popUpWin.add_prog(file)
        prog.download_complete()
        # text='Download complete                ('+("%s" % ctime(os.path.getmtime(file)))+')'


    def history(self):
        sleep(1)
        try:
            data = self.loginwindow.getData()["downloads"]
            for file in data:
                self.addHistory(file)
               
        except Exception as e:
            print("00d", e)
        self.loginwindow.checkVersion()

    def configure_search_result(self, idd):
        self.show_load_pop()
        self.parent.config(cursor='watch')
        self.stop_serch_value=True
        result = self.search_result_youtube.result(mode = ResultMode.dict)
        self.thumbnails.clear()

        thList = []
        
        for v in result['result']:
            if self.stop_config_result != idd:
                break
            t = Thread(target=self.con, args=(v, idd) , daemon=True)
            t.start()
            thList.append(t)
            # self.con(v, idd)
        
        for th in thList:
            th.join()


        self.load_prog.stop()
        self.stop_serch_value = False
        self.parent.config(cursor='')

        self.configAll()
        self.parent.event_generate("<Configure>")
        


    def configAll(self, event=None):
        self.config_internet_animation()
        for widget in self.infoFrameForUpdate:
            widget.config(width=self.root.winfo_width() - 390)


    def con(self, v, idd):
        try:
            thumbnails=(v['thumbnails'][0])['url']
            title_txt=str(v['title'])

            duration=v['duration']
            channel=v['channel']['name']
            channel_icon_url = v['channel']['thumbnails'][0]["url"]
            viewCount = v['viewCount']['short']
            publishedTime =  v['publishedTime']
            try:
                des = v["descriptionSnippet"][0]["text"]
            except:
                des = ""



            self.thumbnails[v['id']] = thumbnails

            response = requests_get(thumbnails)
            load = Image.open(io_import.BytesIO(response.content))
            load=load.resize((360,202),Image.Resampling.LANCZOS)
            image_thumb = ImageTk.PhotoImage(load)


            response = requests_get(channel_icon_url)
            load = Image.open(io_import.BytesIO(response.content))
            size = (35, 35)
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask) 
            draw.ellipse((0, 0) + size, fill=255, outline=10)

            output = ImageOps.fit(load, mask.size, centering=(0.5, 0.5))
            output.putalpha(mask)
            channel_image = ImageTk.PhotoImage(output)


            img_idd = genSessionId(50, self.prevIdd)
            self.prevIdd.append(img_idd)

            icon_img_idd = genSessionId(50, self.prevIdd)
            self.prevIdd.append(icon_img_idd)

            self.imagesData[img_idd] = image_thumb
            self.imagesData[icon_img_idd] = channel_image


            if self.stop_config_result != idd:
                return 0

            container = Frame(self.scrollable_frame, bg=self.back, bd=0)
            container.pack(side='top', anchor='nw', fill='x', expand=True)

            img_container = Canvas(container, bg=self.back, height=202, width=360, bd=0, closeenough=0, highlightthickness=0, confine=1)
            img_container.create_image(0, 10, anchor="nw", image=self.imagesData[img_idd])
            img_container.pack(side='left', ipady=10, anchor='w', padx=20, expand=False)


            duration_info = Label(img_container, text=duration, fg="white", bg="black", font=("", 15, "bold"), justify="left",
                            anchor="w")

            width = duration_info.winfo_reqwidth()

            duration_info.place(x=355-width, y=185)

            info_container = Frame(container, bg=self.back, bd=0, width=self.width - 390)
            info_container.pack(side='left', pady=10, fill="both", anchor="w")
            info_container.pack_propagate(0)
            self.infoFrameForUpdate.append(info_container)

            title = Label(info_container, text=title_txt, fg="#f1f1f1", bg=self.back, font=("yu gothic ui", 24, "bold"), justify="left",
                        anchor="w", wraplength=10)

            title.pack(side='top', fill="x", anchor="n")
            title.bind('<Configure>', lambda e: title.config(wraplength=title.winfo_width()))

            views_info = Label(info_container, text=f"{viewCount} • {publishedTime}", fg="#aaa", bg=self.back, font=("yu gothic ui", 16, "bold"), justify="left",
                            anchor="w")
            views_info.pack(side='top', anchor="nw", padx=3)

            channel_info_text=f"  {channel}"
            channel_info = Label(info_container, compound='left', anchor='w', justify='left', bg=self.back, fg='#aaa', font=('yu gothic ui', 17, 'bold'),
                                image=self.imagesData[icon_img_idd], text=channel_info_text)
            channel_info.pack(side='top', anchor="nw", pady=12)

            description = Label(info_container, text=des, fg="#aaa", bg=self.back, font=("sans-serif", 15, "bold"), justify="left",
                            anchor="w")
            description.pack(side='top', anchor="nw", fill="x")
            description.bind('<Configure>', lambda e: description.config(wraplength=description.winfo_width()))


            container.bind("<Enter>", self.functools_partial(self.enter, container))
            container.bind("<Leave>", self.functools_partial(self.leave, container))
            container.bind('<Double-1>', self.functools_partial(self.dowload_command, v['id'], container))
        
            container.bind("<MouseWheel>",self.scroll_window)

            for child in container.winfo_children():
                child.bind("<Enter>", self.functools_partial(self.enter, container))
                child.bind("<Leave>", self.functools_partial(self.leave, container))
                child.bind('<Double-1>', self.functools_partial(self.dowload_command, v['id'], container))
                child.bind("<MouseWheel>",self.scroll_window)

                for sub_child in child.winfo_children():
                    # sub_child.bind("<Enter>", self.functools_partial(self.enter, container))
                    # sub_child.bind("<Leave>", self.functools_partial(self.leave, container))
                    sub_child.bind('<Double-1>',self.functools_partial(self.dowload_command, v['id'], container))
                    sub_child.bind("<MouseWheel>",self.scroll_window)

            self.parent.update()



        except Exception as e:
            print(f"Error in config result==> {e}")
            return 0
        

        
    def dowload_command(self, idd, widget, event):
        self.parent.config(cursor='watch')
        widget.config(bg='#254454' )
        for child in widget.winfo_children():
            child.config(bg="#254454")

            for sub_child in child.winfo_children():
                sub_child.config(bg="#254454")

        self.video_id=idd

        th=Thread(target=self.call_download_menu,args=(event, widget, self.video_id,), daemon = True)
        th.start()    
         
    def clear_win(self):            
        self.canvas.yview_moveto(0.0)
        self.infoFrameForUpdate.clear()
        for children in self.scrollable_frame.winfo_children():
            children.destroy()

        self.prevIdd.clear()
        self.imagesData.clear()
        self.imagesData.clear()

            
    def scroll_window(self, event):
        self.canvas.yview("scroll",-1*int(event.delta/120),"units")# dhoom dhaam dhosthaan
        
        y = int(self.canvas.canvasy(0))

        h = int(self.scrollable_frame.winfo_height())-900

        if y > h:
            if self.stop_serch_value==False:
                self.stop_serch_value=True
                try:
                    self.search_result_youtube.next()
                    th=Thread(target=self.configure_search_result, args=(self.stop_config_result,), daemon = True)
                    th.start()
                except Exception as e:
                    if not self.loginwindow.isOnline():
                        messagebox.showinfo("YouTube", "     Computer not connected. Make sure your computer has an\n     active Internet Connection")
                    else:
                        messagebox.showerror("YouTube Error 55", f"     {e}")
                    self.stop_serch_value=False
                    
            else:
                pass
            
    def leave(self,widget, event):
        if widget.cget("bg")=='#254454':
            pass
        else:
            widget.config(bg="#0f0f0f")
            for child in widget.winfo_children():
                child.config(bg="#0f0f0f")
                
                for sub_child in child.winfo_children():
                    sub_child.config(bg="#0f0f0f")
        root.update()


    def enter(self, widget, event):
        if widget.cget("bg")=='#254454':
            pass
        else:
            widget.config(bg='grey13' )
            for child in widget.winfo_children():
                child.config(bg="grey13")

                for sub_child in child.winfo_children():
                    sub_child.config(bg="grey13")
        root.update()
        
    

    def call_download_menu(self,event=None, widget=None, i_d=None, tok=False): 

        self.show_load_pop()       
        download_menu = Menu(self.canvas, fg='grey90', bg='grey10', tearoff = 0, font = ('yu gothic ui', 20, "bold"))
        try:
            if "www.youtube.com/watch?v=" in i_d:
                url = i_d
            else:
                url = f"https://www.youtube.com/watch?v={i_d}" 

            video_info, title = get_video_info(url=url)
            print(f"======>{url}")

            length_of_space = self.my_font.measure(" ")

            for quality in video_info:
                lab = f" {quality}  {format_size(video_info[quality]['size'])} "
                text_width = self.my_font.measure(lab)
                space_pxl = (self.max_pixl - text_width) / length_of_space
                lab = f" {quality}  {" " * round(space_pxl) or 5}{format_size(video_info[quality]['size'])} "

                download_menu.add_command(
                    label = lab,
                    #, title = None, audio_size = None, video_size = None,
                    command = self.functools_partial(self.lownload_selected_video, url, video_info[quality]['id'], title, video_info["mp3"]['size'], video_info[quality]['size'])
                    )
                
                if quality == "mp3":
                    download_menu.add_separator()

           
            self.load_prog.stop()
            download_menu.tk_popup(event.x_root, event.y_root)

        except Exception as e:
            self.load_prog.stop()
            if not self.loginwindow.isOnline():
                messagebox.showinfo("YouTube", "     Computer not connected. Make sure your computer has an\n     active Internet Connection")
            else:
                print(f"Error==> {e}")
                messagebox.showerror("YouTube Error 11", f"     {e}")

        finally:
            self.parent.config(cursor='')
            widget.config(bg='#0f0f0f' )
            for child in widget.winfo_children():
                child.config(bg="#0f0f0f")

                for sub_child in child.winfo_children():
                    sub_child.config(bg="#0f0f0f")
        


    def lownload_selected_video(self, url = None, video_id=None, title = None, audio_size = None, video_size = None, video_stream=None, widget=None):
        if video_stream == None:
            video_stream = self.video
            
        th=Thread(target=self.try_download_selected_video, args = (url, video_id, title, audio_size, video_size, video_stream, widget), daemon = True)
        th.start()
        

    def try_download_selected_video(self, url, video_id, title, audio_size, video_size, video_stream, widget, ddir=None):
        # try:                
        self.threading_lownload_selected_video(url, video_id, title, audio_size, video_size, video_stream, widget=widget, ddir=ddir)        
        # except Exception as e:
        #     print('Exception==: ',e)

            

    def create_download_satatus_label(self,name='',progress=0,download_status="(0 KB of 0 MB , 00.0 KB/s)"
                                      ,status=True,file_path=None,file_size=0):

        height=int(self.dwn_canvas['height'])
        parent_height=int(self.root.winfo_height())-250
        if height <= parent_height:
            if height==0:
                self.dwn_canvas['height']=height+85
            else:
                self.dwn_canvas['height']=height+90
                    
       
        progress_label=Frame(self.dwn_scrollable_frame,bg='white',width=535,height=90)
        progress_label.pack(side='bottom')
        progress_label.bind("<MouseWheel>",self.dwn_scroll_window)

        
        progress_bar = Progressbar(progress_label, length=425,style="black.Horizontal.TProgressbar",
                          maximum=file_size, value=0,mode="determinate",orient="horizontal")            
        progress_bar['value'] = progress
        progress_bar.place(x=20,y=35)
        
        video_name=Label(progress_label,text=name,bg='white',fg='black',height=0,font=('',11),anchor="w",
                         width=48)
        video_name.place(x=17,y=2)
        
        time_left=Label(progress_label,text='',bg='white',fg='black',height=0,font=('',9),anchor="w")
        time_left.place(x=17,y=45)
                
        down_status=Label(progress_label,text=download_status,bg='white',fg='black',height=0,font=('',9),anchor="w")
        down_status.place(x=240,y=45)

        pause_resume_label=Label(progress_label,bg='white',fg='black',font=('',9))
        pause_resume_label.place(x=465,y=14)

        pause_download=Button(pause_resume_label,image=self.pause_img,bg='white',relief='sunken',bd=0,
                              highlightbackground='white')                
        resume_download=Button(pause_resume_label,image=self.resume_img,
                               bg='white',relief='sunken',bd=0,highlightbackground='white')
        
        open_folder=Button(progress_label,image=self.folder_img,height=70,width=70,
                               bg='white',relief='sunken',bd=0,highlightbackground='white')
        
        sep=Frame(progress_label,bg='orange3',width=600,height=3)
        sep.place(x=0,y=87)   

        if status==True:
            pause_download.grid(row=0,column=0,ipady=5,ipadx=5)
        else:
            resume_download.grid(row=0,column=0,ipady=5,ipadx=5)
        for widget in progress_label.winfo_children():
            widget.bind("<MouseWheel>",self.dwn_scroll_window)
            

        widget=(progress_label,pause_resume_label,progress_bar,video_name,down_status,time_left,resume_download,
                pause_download,open_folder,file_path)
        
        return  widget
    

    def resume_command(self,video_id,video_stream,widget):
        (progress_label,pause_resume_label,progress_bar,video_name,
         down_status,time_left,resume_download,pause_download,open_folder,file_path)=widget
        resume_download.grid_remove()            
        pause_download.grid(row=0,column=0,ipady=5,ipadx=5)        
        self.lownload_selected_video(video_id,video_stream,widget)

    def open_downloaded_folder(self,path):
        path=path.replace('/','\\')
        subprocess.run(f'explorer /select, "{path}"')
        
    def on_leave(self,event,col):
        event.widget['bg']=col
        for widget in event.widget.winfo_children():
            try:
                if widget['text']=='sep':
                    pass
                else:
                    widget['bg']=col
            except:
                pass
     



    def threading_lownload_selected_video(self, url = None, video_id = None, title = None, audio_size = None, video_size = None, video_stream = None, widget = None, ddir = None):
        self.show_pop_win()
        self.popUpWin.move_to("0.0")
        idd = genSessionId(40, self.down_process_list)
        print(f"Thread--> {idd}")
        self.start_down_animation(idd)

        print(f"url : {url}")
        print(f"video_id : {video_id}")
        print(f"title : {title}")
        print(f"audio_size : {audio_size}")
        print(f"video_size : {video_size}")


        tube = Dtube(title = title)
        tube.url = url
        tube.format_id = video_id # if mp3 then use_only can make this right in optionns

        def pause_command(event=None):
            nonlocal prog, stream_status, widget, video_id, video_stream        
            # pause_download.grid_remove()            
            # resume_download.grid(row=0,column=0,ipady=5,ipadx=5)
            # stream_status=False
            # resume_download.config(command=self.functools_partial(self.resume_command,video_id,
                                                                #   video_stream,widget))

        

        def progress(status : dict):
            # status = {
            #         "status" : "downloading",
            #         "filename" : filename,
            #         "downloaded" : downloaded,
            #         "eta" : time_left,
            #         "progress" : prog_info,
            #     }
            if status['status'] == 'downloading':
                
                prog.update(int(status['downloaded']), status['eta'], status['progress'])




        if video_id == "mp3":
            tube.only_audio = True
            total_size = audio_size

        else:
            total_size = video_size + audio_size

        filename = tube.filename
        file_path = tube.file_path


        if widget == None:
            prog = self.popUpWin.add_prog(file_path)
            prog.update(timest="Fetching info...")
        else:
            prog = widget

        tube.prog = prog

        #Adding_Video_Name_And_Size_To_Status_Bar    
        prog.config(max_size = total_size, pause_cmd = pause_command)

        if video_id =='mp3':
            print("Ideo  ins mp3... so changin icon....")
            prog.config(ext=".mp3")

        stream_status = True

        file_exists_satatus = False

        if video_id =='mp3':
            exists_path=file_path
            print("exists_path==>",exists_path)
            
            if os.path.exists(exists_path):
                print('exists_path==::',exists_path)
                c=messagebox.askquestion(title='Downloading Song.... !',
                message='File already exists in   Music folder\n Do you want to download it again'
                ,icon = 'warning',default='no')
                if c=='yes':
                    try:
                        os.remove(exists_path)
                        file_exists_satatus=False
                    except:
                        file_exists_satatus=True                        
                    
                elif c=="no":
                    file_exists_satatus=True                
            else:
                file_exists_satatus=False
        else:
            
            if os.path.exists(file_path):
                exists_path = file_path
                print('exists_path==::',exists_path)
                c=messagebox.askquestion(title='Downloading Video.... !',
                message='File already exists in   Videos folder\n Do you want to download it again'
                ,icon = 'warning',default='no')
                if c=='yes':
                    try:
                        os.remove(exists_path)
                        file_exists_satatus=False
                    except:
                        file_exists_satatus=True                        
                    
                elif c=="no":
                    file_exists_satatus=True                
            else:
                file_exists_satatus=False
                
        if file_exists_satatus == False:

            # try:
                
            down_info = tube.download()

            # except Exception as e:
            #     if not self.loginwindow.isOnline():
            #         messagebox.showinfo("YouTube", "     Computer not connected. Make sure your computer has an\n     active Internet Connection")
            #     else:
            #         messagebox.showerror("YouTube Error 22", f"     {e}")
            #     return 0
            

            prog.update(value=int(total_size))


            
            if video_id =='mp3':
                # time_left.config(text='Converting...',fg='green')
                prog.update(timest = 'Converting...')
                prog.update(timest = 'Opening.....')

                try:

                    #__Adding_title_and_info ID3,TIT2,TLEN,TCON,TPE1,TALB,TDES,TPUB,WPUB,TDRL,APIC
                    audio = MP3(file_path, ID3=ID3)
                    audio.tags.add(TIT2(encoding=3, text=str(title)))
                    audio.tags.add(TCON(encoding=3, text=str("Music")))
                    audio.tags.add(TPE1(encoding=3, text=str("Aditya Mukhiya")))
                    audio.tags.add(TALB(encoding=3, text=str("M_A_Music_Player__ID: ")))#Album
                    audio.tags.add(TPUB(encoding=3, text=str("Aditya Mukhiya")))
                    audio.tags.add(WPUB(encoding=3, text="Aditya_Mukhiya_M_A_Music_Player"))
                    # adding ID3 tag if it is not present
                    try:
                        audio.add_tags()
                    except Exception as e:
                        print("Error[8994] :", e)
 
                    try:    
                        url_thmb = get_thumbnail(down_info)          
                        response = requests_get(url_thmb)
                        audio.tags.add(APIC(encoding=0,mime='image/jpeg',type=0,desc='',
                                            data=response.content))
                    except Exception as e:
                        print("Error[82394] :", e)
                        
                    # edit ID3 tags to open and read the picture from the path specified and assign it
                    audio.save() # save the current changes
                except Exception as e:
                    print('Error [Adding_tile_to_file]:',e)

                open_file(file_path)
                prog.update(timest='Download Complete')
                
            else:
                prog.update(timest='Converting...')
                ext=(os.path.splitext(file_path)[1])[1:]

                # if not is_progressive:
                
                # best=video_stream.streams.filter(only_audio=True ,file_extension=ext)
                # best=best[len(best)-1]
                # def noop(stream, chunk, bytes_remaining):
                #     pass

                # video_stream.register_on_progress_callback(noop)
                # path_2=os.path.dirname(file_path)+'/Audio__'+os.path.basename(file_path)+"."+ext 
                # best.download(filename=path_2)

                down_info = tube.download()
            
                # file_path=self.add_audio_to_video(file_path, path_2) 
                # else:
                #     print("Progressive... viode no need of audion")


                # video_name.config(text=os.path.basename(file_path))
                prog.update(timest='Opening...')
                prog.config(path=file_path)
                prog.open_file_on_click()
                prog.update(timest='Download Complete')
        else:
            file_path=exists_path
            

##        #deleting_widgets
        prog.download_complete()
        prog.config(path=file_path)

        self.stop_down_animation(idd)
        
        if file_exists_satatus==True:
            prog.update(timest='Already Downloaded')

        else:
            text= f'Download complete ({format_size(total_size)})'
            prog.update(timest=text)

            alldata = self.loginwindow.getData()
            data = alldata["downloads"]
            data.append(file_path)
            alldata["downloads"] = data
            self.loginwindow.writeData(alldata)
            self.download_butn.stop()

        
    def open_file_on_click(self,progress_label,file_path,video_name):
        print("called...")
        open_file(file_path)
        text=os.path.basename(file_path)
        video_name.config(text='Opening  file...',font=('',14,'bold italic'),fg='red2')
        progress_label['bg']='SeaGreen1'
        progress_label.update()
        root.update()
                
        for widget in progress_label.winfo_children():
            try:
                if widget['text'] != 'sep':
                    widget['bg']='SeaGreen1'
                    progress_label.update()
                    root.update()

            except:
                pass
            
        sleep(0.8)
        root.update()
        video_name.config(font=('',14,'bold'),fg='black',text=os.path.basename(file_path))
        root.update()
        progress_label['bg']='cyan'                
        for widget in progress_label.winfo_children():
            try:
                if widget['text']=='cyan':
                    pass
                else:
                    widget['bg']='cyan'
                    progress_label.update()
                    root.update()
            except:
                pass

        



    def add_audio_to_video(self, video, audio):
        name , ext =os.path.splitext(video)
        
        orgName=name+ext
        name=name+'_M_A_Music_PlayerConverting'+ext

        ff_path=resource_path('data/ffmpeg.exe')

        print(f"video==>>>>>>{video} ")
        print(f"name==>>>>>>> {name}")
        print(f"orgName==>>>>>> {orgName}")
        print(f"audio==>>>>>> {audio}")

        task = f'"{ff_path}" -i "{video}" -i "{audio}" -map 0 -map 1 -c copy "{name}"'

        result= subprocess.Popen(task, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
        grep_stdout = result.communicate(input=b'y')[0]
        print("===========>", grep_stdout.decode())

        # os.remove(video)
        # os.remove(audio)
        os.rename(name, orgName)
        print("FimeName==> ",orgName)
        return orgName

    def convert_mp4_to_mp3(self,video):
        name=os.path.splitext(os.path.splitext(video)[0])[0]
        print("Name1==>",name)
        
        ff_path=resource_path('data/ffmpeg.exe')
        task = f'"{ff_path}" -i "{video}"  -q:a 0 -map a "{name}.mp3"'
        result= subprocess.Popen(task,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
        grep_stdout = result.communicate(input=b'y')[0]
        print("===========>", grep_stdout.decode())
    
        try:
            os.remove(video)
        except Exception as e:
            print('Error: In removing_video --',e)
        
        print("Name2==>",name+'.mp3')
        return name+'.mp3'
        

    def close_ffmpeg(self,event=None):
        print('killing')
        cmd=subprocess.run('taskkill /pid ffmpeg.exe /f',shell=True)
        print('killed')     
   




def dark_title_bar(window):
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2
    value = ctypes.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ctypes.byref(value),
                         ctypes.sizeof(value))
    


ctypes.windll.shcore.SetProcessDpiAwareness(True)
loginwindow = LoginPage()


if loginwindow.authenticate():
    print("Authencated.....")
else:
    sys.exit(1)

root = Tk()
dark_title_bar(root)
root.tk.call('tk', 'scaling', 1.0)
root.title('Tube Downloader')
root.geometry(f"{1200}x{800}+{int((root.winfo_screenwidth()/2)-(1100/2))}+{int((root.winfo_screenheight()/2) - (880/2))}")
phototitle = PhotoImage(file =resource_path("data/play3.png"),master=root)
root.iconphoto(True, phototitle)
youtube=YouTube_Download(root, loginwindow, root)
root.bind("<Control-h>",loginwindow.autor)
# root.bind("<Control-l>",logout)
# root.bind("<Control-Shift-f>",feedback )
# root.bind("<Control-Shift-F>",feedback )
root.mainloop()