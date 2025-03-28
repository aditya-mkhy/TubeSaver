import time
from pytube import YouTube ,Playlist
import os
from pathlib import Path
import yt_dlp
import threading
from extra import format_size, timeCal
import json


def get_thumbnail(data: dict):
    thumbnails = data.get("thumbnails", [])
    pref = -100
    url_thmb = ""

    for thumbnail in thumbnails:
        preference = thumbnail.get("preference")
        if preference > pref:
            url = thumbnail.get("url", "")
            _, ext = os.path.splitext(url)
            if ext == ".jpg":
                pref = preference
                url_thmb = url


    return url_thmb


def get_video_info(url : str = None) -> dict:
    if not url:
        raise ValueError(("Url can't be empty..."))
    
    videos_info = {}
    
    ydl_opts = {
        'quiet': True,  # Suppress output
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "no_title")
    
        formats = info.get('formats', [])
        best_audio_format = None


        # audio format....file_size....
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # Audio-only formats
                if not best_audio_format or f.get('filesize', 0) > best_audio_format.get('filesize', 0):
                    best_audio_format = f

        best_audio_size = best_audio_format.get('filesize', 0) if best_audio_format and best_audio_format.get('filesize') else 0
        
        videos_info["mp3"] = {
            "size" : best_audio_size,
            "id" : "mp3",
            "resolution" : "none"
        }

        # Video resolutions....
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get("format_note") != None:
                resolution = f.get('resolution')
                if not resolution:
                    continue

                format_id = f.get('format_id')

                # add audio size into video size 
                # if video is premimum then size = 0
                filesize = f.get('filesize', 0) + best_audio_size if f.get('filesize') else 0
                format_note = f.get('format_note') # quality of the 
                
                if videos_info.get(format_note): #format_note exits in info
                    # filesize is greter video quality is better
                    if videos_info[format_note]["size"] > filesize:
                        continue

                videos_info[format_note] = {
                    "size" : filesize,
                    "id" : format_id,
                    "resolution" : resolution
                }

    return videos_info, title


class Dtube:
    def __init__(self, title: str = None,  path : str = None):
        # for multiple playlist down
        self.down_dir = path
        if self.down_dir == None:
            self.down_dir = str(Path.home())+f'\\Videos'

        self.title = title
        if title == None:
            raise ValueError("Title can't be empty...")

        self.music_dir = f"{str(Path.home())}\\Music"

        self.down_path = self.down_dir


        #settings
        self.url = None
        self.prog = None
        self.only_audio = False

        self.format_id = "bv*"

        self.is_video_dowloaded = False
        self.video_size = 0


    @property
    def file_path(self):
        filename = self.filename
        if self.only_audio:
            return f"{self.music_dir}\\{filename}"
        
        return f"{self.down_dir}\\{filename}"
    

    @property
    def filename(self):
        title_path = self.make_title_path()
        if self.only_audio:
            return f"{title_path}.mp3"
        
        return f"{title_path}.mp4"


    def make_title_path(self, title = None):
        not_include = '<>:"/\\|?*'+"'"
        title_path = ""

        if title == None:
            title = self.title

        for w in title:
            if w in not_include:
                title_path += " "
            else:
                title_path += w

        return title_path

        
    def download(self, url : str = None) -> dict:
        if url != None:
            self.url = url

        if self.url == None:
            raise ValueError("Please provide a video or playlist url....")
        
        if "playlist?list" in self.url:
            print("Getting playlist information.....")
            self.__down_playlist()

        else:
            return self.__video_download(url = self.url)

    def __video_download(self, url, count = "") -> dict:

        ydl_opts = {
            'format': f'{self.format_id}+bestaudio/best',  # Best video + best audio, fallback to best single file
            'merge_output_format': 'mp4',  # Merge the output into an MP4 file
            'progress_hooks': [self.progress_hook],
            'quiet': True,                       # Silence yt_dlp output
            'no_warnings': True, 
            'age_limit' : 25,
            'outtmpl': f'{self.down_path}\\{count}{self.make_title_path()}.%(ext)s',  # Output file name and path
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Convert the final file to MP4 if needed
            }],
        }

        if self.only_audio:
            ydl_opts['format'] = 'bestaudio/best' # Select the best audio format available
            ydl_opts['outtmpl'] = f'{self.music_dir}\\{self.make_title_path()}.%(ext)s'  # Output file name and path
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
                'preferredcodec': 'mp3',     # Convert to MP3
                'preferredquality': '192',   # Set audio quality (192kbps)
            }]


        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)  # Downloads the video
                # with open("dat.json", "w") as tf:
                #     tf.write(json.dumps(info_dict))
                return info_dict

        except Exception as e:
            print(f"An error occurred: {e}")
            return {}


    def __down_playlist(self):
        playlist = Playlist(self.url)

        #create new folder...
        self.__make_PL_dir(playlist)
        print("Total Viodes ==> ", len(playlist.video_urls))
        video_urls, start_indx = self.__get_urls(playlist)

        count = start_indx
        for url in video_urls:
            count_info = f"{count}) "
            print(f"Downloading: {count}")
            self.__video_download(url = url, count = count_info)

            count += 1
            

    def __get_urls(self, playlist: Playlist):
        
        start =   input("Start index : ")
        try:
            start = int(start)
            # if in negative then down all videos
            if start < 0:
                return playlist.video_urls, 1

            if start == 0:
                start += 1

            end = int(input("End index   : "))
            video_ulrs = playlist.video_urls[start - 1 : end]
            return (video_ulrs, start)

        except:
            print(f"ErrorInIndexing...[{start} : {end}]")
            exit()


    def __make_PL_dir(self, playlist : Playlist):
        notInc = '<>:"/\\|?*'+"'"
        dirname = ""
        try:
            for w in playlist.title:
                if w not in notInc:
                    dirname += w
        except Exception as e:
            dirname = ""

        if dirname == "": 
            print("Can't create a seprate diretory. Using the default...")
            return
        
        down_dir = f"{self.down_dir}\\{dirname}"
        if not os.path.exists(down_dir):
            try:
                os.mkdir(down_dir)
                self.down_path = down_dir

            except Exception as e:
                print(e)
                print("Can't create a seprate diretory. Using the default...")
                self.down_path = down_dir # using default dir
        
        else:
            #if dir is already exits
            self.down_path = down_dir
        
        print("DownPath : ", self.down_path)
    
    def progress(self, status : dict):
        # status = {
        #         "status" : "downloading",
        #         "filename" : filename,
        #         "downloaded" : downloaded,
        #         "eta" : time_left,
        #         "progress" : prog_info,
        #     }
        if status['status'] == 'downloading':
            self.prog.update(int(status['downloaded']), status['eta'], status['progress'])

    def progress_hook(self, d):
        """
        Hook function to display progress during the download.
        """
    
        try:
            if d['status'] == 'downloading':

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', d.get('total_bytes_estimate', 0))
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                filename = d.get('filename', '')
                tmpfilename = d.get('tmpfilename', '')

                if not self.is_video_dowloaded:
                    self.video_size = total

                else:
                    #update the musicccc...
                    downloaded += self.video_size
                    total += self.video_size


                time_left = f"{timeCal(eta)} left"
                speed = format_size(speed)
                prog_info = "(%s of  %s ,  %s)" %(format_size(downloaded) , format_size(total), speed)


                status = {
                    "status" : "downloading",
                    "filename" : filename,
                    "downloaded" : downloaded,
                    "eta" : time_left,
                    "progress" : prog_info,
                }

                self.progress(status)


            elif d['status'] == 'finished':
                filename = d.get('filename', '')

                status = {
                    "status" : "finished",
                    "filename" : filename
                }

                if not self.is_video_dowloaded:
                    self.is_video_dowloaded = True
                
                self.progress(status)


            elif d['status'] == 'error':
                status = {
                    "status" : "error",
                }
    
                self.progress(status)

        except:
            pass

    
   
        

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=4AtnNKglCY0"
    # url  = "https://www.youtube.com/playlist?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"#shradha

    title = "south movies 2"
    tube  = Dtube(title=title)

    # tube.only_audio = True
    pth = tube.file_path
    print(pth)

    # exit()
    

    # for url in urls:
    # # while True:
    #     # url = input("url -> ")
    # url = "https://www.youtube.com/watch?v=kcvDPUZer7I"
    # format_id = 616
    info = tube.download(url=url)
    # url = 
    print(info)
    # info , title = get_video_info(url = url)
    # print("title ==> ", title)
    # print(info)

