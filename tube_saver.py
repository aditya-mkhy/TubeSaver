from util import resource_path, timeCal, format_size, DB, is_online, genSessionId
import os
import sys
import subprocess
import ctypes
import io as io_import

from json import loads, dump
from random import choice, randint
from time import time, sleep, ctime
from pathlib import Path
from threading import Thread
from webbrowser import open as open_file

from tkinter import *
from tkinter import messagebox, font
from tkinter.ttk import Style as ttk_Style, Progressbar, Scale as ttk_Scale

from requests import get as requests_get
from PIL import ImageTk, Image, ImageOps, ImageDraw
from youtubesearchpython import VideosSearch, ResultMode  # pip install youtube-search-python

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TLEN, TCON, TPE1, TALB, TDES, TPUB, WPUB, TDRL, APIC

from popup import DownloadsInfoWin, LoadPopUp, AnimeleButton, AnimeleLabel
from utube import get_video_info, Dtube, get_thumbnail


class YouTube_Download:
    def __init__(self, parent_window: Tk):
        self.width = 1200
        self.height = 800

        # lightweight database..
        self.db = DB()

        self.parent = parent_window
        self.root = parent_window

        # search / results state
        self.video_image_list = []
        self.video_id = None
        self.stop_serch_value = False
        self.stop_config_result = False

        self.entry_var = StringVar()
        self.functools_partial = __import__("functools").partial
        self.video = None
        self.show_down_status_frame = False

        self.version = "10.3.0"
        self.thumbnails = {}
        self.thumbnails_icon = {}
        self.infoFrameForUpdate = []
        self.numHistory = 10
        self.down_process_list = []
        self.no_internet_animation_is_active = False

        # Downloads popup window
        self.popUpWin = DownloadsInfoWin(
            width=630,
            height=645,
            clear_but_cmd=self.clear_download_history,
        )

        # ----------------- TOP SEARCH BAR -----------------
        self.label = Frame(self.parent, bg="grey20")
        self.label.pack(side="top", fill="x")

        self.entry_wgt = Entry(
            self.label,
            textvariable=self.entry_var,
            fg="#0065ff",
            bg="grey17",
            font=("yu gothic ui", 24, "bold"),
            bd=2,
            relief="sunken",
            insertbackground="grey70",
        )
        self.entry_wgt.pack(
            side="left", fill="x", padx=6, expand=True, pady=6, ipadx=1, ipady=1
        )

        self.entry_var.set("Search")

        self.entry_wgt.bind("<Return>", self.search_entry)
        self.entry_wgt.bind("<FocusIn>", self.focus_in_entry_widget)
        self.entry_wgt.bind("<FocusOut>", self.focus_out_entry_widget)

        self.download_image = PhotoImage(
            file=resource_path("data/download.png"), master=self.parent
        )

        self.download_butn = AnimeleButton(
            self.label,
            bg="grey20",
            bd=0,
            highlightbackground="grey20",
            activebackground="grey20",
            command=self.show_pop_win,
            cursor="hand2",
        )
        self.download_butn.pack(side="left", padx=30)

        self.download_butn.__load__(resource_path("data/download.gif"))
        self.download_butn.stop()
        self.download_butn.bind("<Enter>", lambda e: self.start_down_animation(None))
        self.download_butn.bind("<Leave>", lambda e: self.stop_down_animation(None))

        self.back = "#0f0f0f"

        # ----------------- MAIN SCROLL CANVAS -----------------
        self.canvas = Canvas(
            self.root,
            bg=self.back,
            bd=0,
            closeenough=0,
            highlightthickness=0,
            confine=1,
        )
        self.canvas.pack(side="top", fill="both", expand=True, anchor="nw")

        self.scrollable_frame = Frame(self.canvas, bg=self.back, pady=8)
        self.parent.bind("<Configure>", self.configAll)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # progress style
        self.style_Scale = ttk_Style(self.parent)
        self.style_Scale.theme_use("alt")
        self.style_Scale.configure(
            "black.Horizontal.TProgressbar", background="royalblue", thickness=4
        )

        self.parent.bind_all("<Control-Shift-r>", self.close_ffmpeg)
        self.parent.bind_all("<Control-Shift-R>", self.close_ffmpeg)

        self.pause_img = PhotoImage(
            file=resource_path("data/download_pause.png"), master=self.parent
        )
        self.resume_img = PhotoImage(
            file=resource_path("data/download_resume.png"), master=self.parent
        )
        self.folder_img = PhotoImage(
            file=resource_path("data/folder.png"), master=self.parent
        )
        self.folder_img = self.folder_img.subsample(3, 3)

        # ---- misc state ----
        self.root_width_saved = 0
        self.imagesData = {}
        self.prevIdd = []

        self.max_pixl = 240
        self.my_font = font.Font(family="yu gothic ui", size=20, weight="bold")

        # loader popup
        gif_path = resource_path("data/load.gif")
        self.load_prog = LoadPopUp(gif_path, self.parent)
        self.load_prog.set_dely(20)

        # start search on open
        Thread(target=self.on_start_search, daemon=True).start()

    # =====================================================================
    # UI helpers / animations / history
    # =====================================================================

    def start_down_animation(self, idd=None):
        print(f"idd==> {idd}")
        if self.down_process_list == []:
            self.download_butn.play()
            print("Animation starts")
        else:
            print("Animations is already running....")

        if idd:
            print("Process is added")
            self.down_process_list.append(idd)
        else:
            print("This is an enter event")

    def stop_down_animation(self, idd=None):
        print(f"idd==> {idd}")
        if idd:
            if idd in self.down_process_list:
                self.down_process_list.remove(idd)
                print(f"Idd is removed==> {idd}")
        else:
            print("This is a leave event....")

        if self.down_process_list == []:
            self.download_butn.stop()
            print(f"Stopping the animation==> {self.down_process_list}")
        else:
            print(f"Other processes exist==> {self.down_process_list}")

    def clear_download_history(self):
        try:
            self.db["down"] = []
            return True
        except Exception:
            return False

    def no_internet_animation(self):
        self.no_con_anime_path = resource_path("data/offline.gif")
        self.no_connection_anime = AnimeleLabel(
            self.scrollable_frame, bd=0, bg=self.back, compound="center"
        )
        self.no_connection_anime.__load__(self.no_con_anime_path)
        self.no_connection_anime.play()
        self.no_internet_animation_is_active = True
        self.no_connection_anime.pack(
            side="top", fill="both", expand=True, padx=280, pady=50
        )

    def config_internet_animation(self):
        if self.no_internet_animation_is_active:
            x = (self.root.winfo_width() // 2) - 300
            y = (self.root.winfo_height() // 2) - 360
            try:
                self.no_connection_anime.pack_configure(padx=x, pady=y)
            except Exception:
                pass

    def on_start_search(self):
        self.search("hum dum")
        self.history()

    def focus_in_entry_widget(self, event):
        self.entry_wgt.config(fg="#0065ff", font=("yu gothic ui", 24, "bold"))
        d = self.entry_var.get()
        if d in ("Search", "YouTube"):
            self.entry_var.set("")

    def focus_out_entry_widget(self, event):
        d = self.entry_var.get()
        if d.strip() == "":
            self.entry_var.set("Search")
            self.entry_wgt.config(fg="#0065ff", font=("yu gothic ui", 24, "bold"))

    # =====================================================================
    # History
    # =====================================================================

    def addHistory(self, file: str):
        prog = self.popUpWin.add_prog(file)
        prog.download_complete()

    def history(self):
        sleep(1)
        try:
            data = self.db.get("down")
            for file in data:
                self.addHistory(file)
        except Exception as e:
            print("Error [History] => ", e)

    # =====================================================================
    # Search & Scroll
    # =====================================================================

    def search_entry(self, event=None):
        video_name = self.entry_var.get()
        if "www.youtube.com/playlist?" in video_name:
            print("Not supported (playlist)...")
            return

        elif "www.youtube.com/watch?v=" in video_name:
            print("Video link found... Downloading....")
            t = Thread(
                target=self.call_download_menu, args=(event, None, video_name), daemon=True
            )
            t.start()

        else:
            self.search(video_name)

    def show_load_pop(self):
        print("Showing loading popup...")
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
        self.load_prog.show(x, y)

    def show_pop_win(self, st=None):
        x = self.root.winfo_x()
        y = self.root.winfo_y()

        x1 = self.download_butn.winfo_x() + self.download_butn.winfo_width() + 20
        y1 = self.download_butn.winfo_y() + self.download_butn.winfo_height() + 55

        self.popUpWin.pop(x + x1, y + y1)

    def search(self, video_name: str):
        print(f"Search video --> {video_name}")
        try:
            self.video_image_list = []
            self.stop_config_result = randint(100, 10000000)

            self.entry_wgt.unbind("<Return>")
            self.entry_wgt.config(insertontime=0)

            self.search_result_youtube = VideosSearch(video_name, region="IN")
            self.no_internet_animation_is_active = False

            try:
                self.clear_win()
            except Exception as e:
                print(f"Error in cleaning window: {e}")

            th = Thread(
                target=self.configure_search_result,
                args=(self.stop_config_result,),
                daemon=True,
            )
            th.start()

        except Exception as e:
            if not is_online():
                if not self.no_internet_animation_is_active:
                    self.no_internet_animation()
                messagebox.showinfo(
                    "YouTube",
                    "     Computer not connected. Make sure your computer has an\n"
                    "     active Internet Connection",
                )
            else:
                messagebox.showerror("YouTube Error 44", f"     {e}")

        finally:
            self.entry_wgt.config(insertontime=300)
            self.entry_wgt.bind("<Return>", self.search_entry)

    def configure_search_result(self, idd):
        self.show_load_pop()
        self.parent.config(cursor="watch")
        self.stop_serch_value = True

        result = self.search_result_youtube.result(mode=ResultMode.dict)
        self.thumbnails.clear()

        thList = []

        for v in result["result"]:
            if self.stop_config_result != idd:
                break
            t = Thread(target=self.config, args=(v, idd), daemon=True)
            t.start()
            thList.append(t)

        for th in thList:
            th.join()

        self.load_prog.stop()
        self.stop_serch_value = False
        self.parent.config(cursor="")

        self.configAll()
        self.parent.event_generate("<Configure>")

    def configAll(self, event=None):
        self.config_internet_animation()
        for widget in self.infoFrameForUpdate:
            widget.config(width=self.root.winfo_width() - 390)

    def clear_win(self):
        self.canvas.yview_moveto(0.0)
        self.infoFrameForUpdate.clear()
        for children in self.scrollable_frame.winfo_children():
            children.destroy()

        self.prevIdd.clear()
        self.imagesData.clear()

    def scroll_window(self, event):
        self.canvas.yview("scroll", -1 * int(event.delta / 120), "units")

        y = int(self.canvas.canvasy(0))
        h = int(self.scrollable_frame.winfo_height()) - 900

        if y > h:
            if self.stop_serch_value is False:
                self.stop_serch_value = True
                try:
                    self.search_result_youtube.next()
                    th = Thread(
                        target=self.configure_search_result,
                        args=(self.stop_config_result,),
                        daemon=True,
                    )
                    th.start()
                except Exception as e:
                    if not is_online():
                        messagebox.showinfo(
                            "YouTube",
                            "     Computer not connected. Make sure your computer has an\n"
                            "     active Internet Connection",
                        )
                    else:
                        messagebox.showerror("YouTube Error 55", f"     {e}")
                    self.stop_serch_value = False
            else:
                pass

    # =====================================================================
    # Result item creation + hover
    # =====================================================================

    def config(self, v, idd):
        try:
            thumbnails = (v["thumbnails"][0])["url"]
            title_txt = str(v["title"])

            duration = v["duration"]
            channel = v["channel"]["name"]
            channel_icon_url = v["channel"]["thumbnails"][0]["url"]
            viewCount = v["viewCount"]["short"]
            publishedTime = v["publishedTime"]
            try:
                des = v["descriptionSnippet"][0]["text"]
            except Exception:
                des = ""

            self.thumbnails[v["id"]] = thumbnails

            # video thumbnail
            response = requests_get(thumbnails)
            load = Image.open(io_import.BytesIO(response.content))
            load = load.resize((360, 202), Image.Resampling.LANCZOS)
            image_thumb = ImageTk.PhotoImage(load)

            # channel icon (rounded)
            response = requests_get(channel_icon_url)
            load = Image.open(io_import.BytesIO(response.content))
            size = (35, 35)
            mask = Image.new("L", size, 0)
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
            container.pack(side="top", anchor="nw", fill="x", expand=True)

            img_container = Canvas(
                container,
                bg=self.back,
                height=202,
                width=360,
                bd=0,
                closeenough=0,
                highlightthickness=0,
                confine=1,
            )
            img_container.create_image(0, 10, anchor="nw", image=self.imagesData[img_idd])
            img_container.pack(side="left", ipady=10, anchor="w", padx=20, expand=False)

            duration_info = Label(
                img_container,
                text=duration,
                fg="white",
                bg="black",
                font=("", 15, "bold"),
                justify="left",
                anchor="w",
            )

            width = duration_info.winfo_reqwidth()
            duration_info.place(x=355 - width, y=185)

            info_container = Frame(
                container, bg=self.back, bd=0, width=self.width - 390
            )
            info_container.pack(side="left", pady=10, fill="both", anchor="w")
            info_container.pack_propagate(0)
            self.infoFrameForUpdate.append(info_container)

            title = Label(
                info_container,
                text=title_txt,
                fg="#f1f1f1",
                bg=self.back,
                font=("yu gothic ui", 24, "bold"),
                justify="left",
                anchor="w",
                wraplength=10,
            )

            title.pack(side="top", fill="x", anchor="n")
            title.bind(
                "<Configure>",
                lambda e: title.config(wraplength=title.winfo_width()),
            )

            views_info = Label(
                info_container,
                text=f"{viewCount} • {publishedTime}",
                fg="#aaa",
                bg=self.back,
                font=("yu gothic ui", 16, "bold"),
                justify="left",
                anchor="w",
            )
            views_info.pack(side="top", anchor="nw", padx=3)

            channel_info_text = f"  {channel}"
            channel_info = Label(
                info_container,
                compound="left",
                anchor="w",
                justify="left",
                bg=self.back,
                fg="#aaa",
                font=("yu gothic ui", 17, "bold"),
                image=self.imagesData[icon_img_idd],
                text=channel_info_text,
            )
            channel_info.pack(side="top", anchor="nw", pady=12)

            description = Label(
                info_container,
                text=des,
                fg="#aaa",
                bg=self.back,
                font=("sans-serif", 15, "bold"),
                justify="left",
                anchor="w",
            )
            description.pack(side="top", anchor="nw", fill="x")
            description.bind(
                "<Configure>",
                lambda e: description.config(wraplength=description.winfo_width()),
            )

            container.bind("<Enter>", self.functools_partial(self.enter, container))
            container.bind("<Leave>", self.functools_partial(self.leave, container))
            container.bind(
                "<Double-1>",
                self.functools_partial(self.dowload_command, v["id"], container),
            )

            container.bind("<MouseWheel>", self.scroll_window)

            for child in container.winfo_children():
                child.bind("<Enter>", self.functools_partial(self.enter, container))
                child.bind("<Leave>", self.functools_partial(self.leave, container))
                child.bind(
                    "<Double-1>",
                    self.functools_partial(self.dowload_command, v["id"], container),
                )
                child.bind("<MouseWheel>", self.scroll_window)

                for sub_child in child.winfo_children():
                    sub_child.bind(
                        "<Double-1>",
                        self.functools_partial(self.dowload_command, v["id"], container),
                    )
                    sub_child.bind("<MouseWheel>", self.scroll_window)

            self.parent.update()

        except Exception as e:
            print(f"Error in config result==> {e}")
            return 0

    def leave(self, widget, event):
        if widget.cget("bg") == "#254454":
            return
        widget.config(bg="#0f0f0f")
        for child in widget.winfo_children():
            child.config(bg="#0f0f0f")
            for sub_child in child.winfo_children():
                sub_child.config(bg="#0f0f0f")
        self.root.update()

    def enter(self, widget, event):
        if widget.cget("bg") == "#254454":
            return
        widget.config(bg="grey13")
        for child in widget.winfo_children():
            child.config(bg="grey13")
            for sub_child in child.winfo_children():
                sub_child.config(bg="grey13")
        self.root.update()

    # =====================================================================
    # Download menu + pipeline
    # =====================================================================

    def dowload_command(self, idd, widget, event):
        self.parent.config(cursor="watch")
        widget.config(bg="#254454")
        for child in widget.winfo_children():
            child.config(bg="#254454")
            for sub_child in child.winfo_children():
                sub_child.config(bg="#254454")

        self.video_id = idd

        th = Thread(
            target=self.call_download_menu,
            args=(event, widget, self.video_id),
            daemon=True,
        )
        th.start()

    def call_download_menu(self, event=None, widget=None, i_d=None, tok=False):
        self.show_load_pop()
        download_menu = Menu(
            self.canvas,
            fg="grey90",
            bg="grey10",
            tearoff=0,
            font=("yu gothic ui", 20, "bold"),
        )
        try:
            if i_d and "www.youtube.com/watch?v=" in i_d:
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
                lab = (
                    f" {quality}  "
                    f"{' ' * (round(space_pxl) or 5)}"
                    f"{format_size(video_info[quality]['size'])} "
                )

                download_menu.add_command(
                    label=lab,
                    command=self.functools_partial(
                        self.lownload_selected_video,
                        url,
                        video_info[quality]["id"],
                        title,
                        video_info["mp3"]["size"],
                        video_info[quality]["size"],
                    ),
                )

                if quality == "mp3":
                    download_menu.add_separator()

            self.load_prog.stop()
            download_menu.tk_popup(event.x_root, event.y_root)

        except Exception as e:
            self.load_prog.stop()
            if not is_online():
                messagebox.showinfo(
                    "YouTube",
                    "     Computer not connected. Make sure your computer has an\n"
                    "     active Internet Connection",
                )
            else:
                print(f"Error==> {e}")
                messagebox.showerror("YouTube Error 11", f"     {e}")

        finally:
            self.parent.config(cursor="")
            if widget is not None:
                widget.config(bg="#0f0f0f")
                for child in widget.winfo_children():
                    child.config(bg="#0f0f0f")
                    for sub_child in child.winfo_children():
                        sub_child.config(bg="#0f0f0f")

    def lownload_selected_video(
        self,
        url=None,
        video_id=None,
        title=None,
        audio_size=None,
        video_size=None,
        video_stream=None,
        widget=None,
    ):
        if video_stream is None:
            video_stream = self.video

        th = Thread(
            target=self.try_download_selected_video,
            args=(url, video_id, title, audio_size, video_size, video_stream, widget),
            daemon=True,
        )
        th.start()

    def try_download_selected_video(
        self,
        url,
        video_id,
        title,
        audio_size,
        video_size,
        video_stream,
        widget,
        ddir=None,
    ):
        self.threading_lownload_selected_video(
            url, video_id, title, audio_size, video_size, video_stream, widget=widget, ddir=ddir
        )

    def threading_lownload_selected_video(
        self,
        url=None,
        video_id=None,
        title=None,
        audio_size=None,
        video_size=None,
        video_stream=None,
        widget=None,
        ddir=None,
    ):
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

        tube = Dtube(title=title)
        tube.url = url
        tube.format_id = video_id

        def pause_command(event=None):
            nonlocal prog, video_id, video_stream, widget

        if video_id == "mp3":
            tube.only_audio = True
            total_size = audio_size
        else:
            total_size = video_size + audio_size

        filename = tube.filename
        file_path = tube.file_path

        if widget is None:
            prog = self.popUpWin.add_prog(file_path)
            prog.update(timest="Fetching info...")
        else:
            prog = widget

        tube.prog = prog

        # configure status bar
        prog.config(max_size=total_size, pause_cmd=pause_command)

        if video_id == "mp3":
            prog.config(ext=".mp3")

        file_exists_satatus = False

        # existence checks
        if video_id == "mp3":
            exists_path = file_path
            print("exists_path==>", exists_path)

            if os.path.exists(exists_path):
                print("exists_path==::", exists_path)
                c = messagebox.askquestion(
                    title="Downloading Song.... !",
                    message=(
                        "File already exists in   Music folder\n "
                        "Do you want to download it again"
                    ),
                    icon="warning",
                    default="no",
                )
                if c == "yes":
                    try:
                        os.remove(exists_path)
                        file_exists_satatus = False
                    except Exception:
                        file_exists_satatus = True
                elif c == "no":
                    file_exists_satatus = True
            else:
                file_exists_satatus = False

        else:
            if os.path.exists(file_path):
                exists_path = file_path
                print("exists_path==::", exists_path)
                c = messagebox.askquestion(
                    title="Downloading Video.... !",
                    message=(
                        "File already exists in   Videos folder\n "
                        "Do you want to download it again"
                    ),
                    icon="warning",
                    default="no",
                )
                if c == "yes":
                    try:
                        os.remove(exists_path)
                        file_exists_satatus = False
                    except Exception:
                        file_exists_satatus = True
                elif c == "no":
                    file_exists_satatus = True
            else:
                file_exists_satatus = False

        if file_exists_satatus is False:
            down_info = tube.download()
            prog.update(value=int(total_size))

            if video_id == "mp3":
                prog.update(timest="Converting...")
                prog.update(timest="Opening.....")

                try:
                    # add ID3 tags
                    audio = MP3(file_path, ID3=ID3)
                    audio.tags.add(TIT2(encoding=3, text=str(title)))
                    audio.tags.add(TCON(encoding=3, text=str("Music")))
                    audio.tags.add(TPUB(encoding=3, text=str("Aditya")))

                    try:
                        audio.add_tags()
                    except Exception as e:
                        print("Error[ID3_add_tag] :", e)

                    try:
                        url_thmb = get_thumbnail(down_info)
                        response = requests_get(url_thmb)
                        audio.tags.add(
                            APIC(
                                encoding=0,
                                mime="image/jpeg",
                                type=0,
                                desc="",
                                data=response.content,
                            )
                        )
                    except Exception as e:
                        print("Error[thumbnail_to_mp3] :", e)

                    audio.save()
                except Exception as e:
                    print("Error [Adding_title_to_file]:", e)

                open_file(file_path)
                prog.update(timest="Download Complete")

            else:
                prog.update(timest="Converting...")
                ext = (os.path.splitext(file_path)[1])[1:]

                down_info = tube.download()

                prog.update(timest="Opening...")
                prog.config(path=file_path)
                prog.open_file_on_click()
                prog.update(timest="Download Complete")
        else:
            file_path = exists_path

        prog.download_complete()
        prog.config(path=file_path)

        self.stop_down_animation(idd)

        if file_exists_satatus is True:
            prog.update(timest="Already Downloaded")
        else:
            text = f"Download complete ({format_size(total_size)})"
            prog.update(timest=text)

            down = self.db.get("down")
            down.append(file_path)
            self.db["down"] = down
            self.download_butn.stop()

    # =====================================================================
    # Extra helpers / ffmpeg
    # =====================================================================

    def add_audio_to_video(self, video, audio):
        name, ext = os.path.splitext(video)

        orgName = name + ext
        name = name + "_M_A_Music_PlayerConverting" + ext

        ff_path = resource_path("data/ffmpeg.exe")

        print(f"video==>>>>>>{video} ")
        print(f"name==>>>>>>> {name}")
        print(f"orgName==>>>>>> {orgName}")
        print(f"audio==>>>>>> {audio}")

        task = f'"{ff_path}" -i "{video}" -i "{audio}" -map 0 -map 1 -c copy "{name}"'

        result = subprocess.Popen(
            task,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        grep_stdout = result.communicate(input=b"y")[0]
        print("===========>", grep_stdout.decode())

        os.rename(name, orgName)
        print("FileName==> ", orgName)
        return orgName

    def convert_mp4_to_mp3(self, video):
        name = os.path.splitext(os.path.splitext(video)[0])[0]
        print("Name1==>", name)

        ff_path = resource_path("data/ffmpeg.exe")
        task = f'"{ff_path}" -i "{video}"  -q:a 0 -map a "{name}.mp3"'
        result = subprocess.Popen(
            task,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        grep_stdout = result.communicate(input=b"y")[0]
        print("===========>", grep_stdout.decode())

        try:
            os.remove(video)
        except Exception as e:
            print("Error: In removing_video --", e)

        print("Name2==>", name + ".mp3")
        return name + ".mp3"

    def close_ffmpeg(self, event=None):
        print("killing ffmpeg...")
        subprocess.run("taskkill /im ffmpeg.exe /f", shell=True)
        print("killed")


# =====================================================================
# Window helpers & main entry
# =====================================================================

def dark_title_bar(window):
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = ctypes.c_int(2)
    set_window_attribute(
        hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value)
    )


ctypes.windll.shcore.SetProcessDpiAwareness(True)


if __name__ == "__main__":
    root = Tk()
    dark_title_bar(root)

    root.tk.call("tk", "scaling", 1.0)
    root.title("Tube Downloader")

    root.geometry(
        f"{1200}x{800}+"
        f"{int((root.winfo_screenwidth()/2)-(1100/2))}+"
        f"{int((root.winfo_screenheight()/2) - (880/2))}"
    )

    phototitle = PhotoImage(
        file=resource_path("data/play3.png"), master=root
    )
    root.iconphoto(True, phototitle)

    youtube = YouTube_Download(root)
    root.mainloop()
