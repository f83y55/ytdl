import json
import urllib.request
import urllib.parse
import re
import os
import youtube_dl
# sudo pip3 install youtube-dl
import base64
from mutagen.easyid3 import EasyID3
# sudo apt install python3-mutagen
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC, Picture
import tkinter as tk
from tkinter import ttk
import webbrowser
import threading

class Playlist :
    FIELDS =    [
                {"name" : "url",         "type" : "entry",  "copy" : False, "default" : ""},
                {"name" : "tracknumber", "type" : "entry",  "copy" : False, "default" : ""},
                {"name" : "title",       "type" : "entry",  "copy" : False, "default" : ""},
                {"name" : "artist",      "type" : "entry",  "copy" : True,  "default" : ""},
                {"name" : "album",       "type" : "entry",  "copy" : True,  "default" : ""},
                {"name" : "date",        "type" : "entry",  "copy" : True,  "default" : ""},
                {"name" : "duration",    "type" : "hidden", "copy" : False, "default" : 0},
                {"name" : "folder",      "type" : "entry",  "copy" : True,  "default" : "tracks"},
                {"name" : "filename",    "type" : "entry",  "copy" : False, "default" : "record"},
                ]
    
    RELATION =  [[el["type"], el["name"]] for el in FIELDS]
    
    CODECS =    [
                {"name" : "MP3 320",    "codec" : "mp3",    "ext" : "mp3",  "quality" : "320", "EmbedThumbnail" : True },
                {"name" : "MP3 240",    "codec" : "mp3",    "ext" : "mp3",  "quality" : "240", "EmbedThumbnail" : True },
                {"name" : "MP3 192",    "codec" : "mp3",    "ext" : "mp3",  "quality" : "192", "EmbedThumbnail" : True },
                #{"name" : "MP4 320",    "codec" : "m4a",    "ext" : "m4a",  "quality" : "320", "EmbedThumbnail" : True },
                {"name" : "Vorbis 256", "codec" : "vorbis", "ext" : "ogg",  "quality" : "256", "EmbedThumbnail" : False },
                {"name" : "Vorbis 128", "codec" : "vorbis", "ext" : "ogg",  "quality" : "128", "EmbedThumbnail" : False },
                {"name" : "Vorbis 64",  "codec" : "vorbis", "ext" : "ogg",  "quality" : "64",  "EmbedThumbnail" : False },
                {"name" : "Flac",       "codec" : "flac",   "ext" : "flac", "quality" : "0",   "EmbedThumbnail" : False },
                ]
    
    def __init__(self):
        self.records = []
        self.settings = {
                        "playlist_url" : "",
                        "tracks_filename" : "tracks",
                        "log_lines" : 8,
                        "query_mask" : "{artist} {title}",
                        "folder_mask" : "{artist} - {album} - {date}",
                        "filename_mask" : "{tracknumber} - {title}",
                        "temp_mask" : "{tracknumber} - {title} - {artist} - {album} - {date}",
                        "codec_chosen" : Playlist.CODECS[0],
                        "max_dl" : "20"
                        }
        self.log = {"log" : ""}
        self.debug = self.tolog
        self.warning = self.tolog
        self.error = self.tolog
        
    def tolog(self, st) :
        print('log : ', st)
        self.log["log"] = "\n".join(f"{self.log['log']}{st}".splitlines()[-self.settings["log_lines"]:])+"\n"
        
    def new_record(self, from_record={}) :
        record = {}
        for field in Playlist.FIELDS :
            if field["name"] in from_record.keys() :
                record[field["name"]] = from_record[field["name"]]
            else :               
                record[field["name"]] = field["default"]
            
        self.tolog("New record")
        return record
        
    def add_record(self, record):
        self.tolog(f"Adding : {record}") 
        self.records.append(record)
        
    def insert_record(self, record, i=0):
        if i <= len(self.records) :
            self.tolog(f"Adding at {i} : {record}") 
            self.records.insert(i, record)

    def collect_playlist(self, url, export_playlist=False, index=None) :
        self.tolog(f"Collect playlist : {url}")
        if url.count("youtube.com/") == 1 :
            self.collect_playlist_youtube(url, auto_search=False, export_playlist=export_playlist, index=index)
        if url.count("open.spotify.com") == 1 :            
            self.collect_playlist_spotify(url, auto_search=True, export_playlist=export_playlist, index=index)
        if url == "" :
            self.add_record(self.new_record())
        self.tolog(f"Collect playlist : done")
 
    def collect_playlist_youtube(self, url, auto_search=False, export_playlist=False, index=None) :
        if index==None :
            index = len(self.records)
        try :
            ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s', 'quiet':False, 'logger':self})
            with ydl :
                result = ydl.extract_info(url, download=False)
                if isinstance(result, dict) :
                    if "playlist" in result.keys() and result["playlist"] : 
                        name_pls = valid_filename(result["playlist"])
                    else :
                        name_pls = valid_filename(url)
                    if export_playlist :
                        try :
                            with open(valid_filename(f"Playlist Youtube - {name_pls}.json"), 'w', encoding='utf-8') as file :
                                json.dump(result, file, indent=4)
                                self.tolog("Playlist exported")
                        except Exception as e :
                            self.tolog(f"Exception : {e}")
                    if "entries" in result and isinstance(result["entries"], list):
                        ls = result["entries"]
                    else : 
                        ls = [result] 
                    digits = max(2, len(str(len(ls))))
                    for tracknumber, item in enumerate(ls, start=1) :
                        record = self.new_record()
                        if "webpage_url" in item.keys() : 
                            record["url"] = item["webpage_url"]
                        record["tracknumber"] = f"{(tracknumber):0{digits}d}"
                        if "track" in item.keys() : 
                            record["title"] = item["track"]
                        if "title" in item.keys() : 
                            record["title"] = item["title"]
                        if "uploader" in item.keys() :
                            record["artist"] = item["uploader"]
                        if "artist" in item.keys() : 
                            record["artist"] = item["artist"]
                        if "playlist" in item.keys() : 
                            record["album"] = item["playlist"]
                        if "album" in item.keys() :
                            record["album"] = item["album"]
                        if "release_year" in item.keys() : 
                            record["date"] = str(item["release_year"])
                        if "duration" in item.keys() : 
                            record["duration"] = item["duration"]
                        record["folder"] = valid_filename(self.settings["folder_mask"].format(**record))
                        record["filename"] = valid_filename(self.settings["filename_mask"].format(**record))
                        if auto_search :
                            query = self.settings["query_mask"].format(**record)            
                            self.tolog(f"Url auto query : {query}")
                            record["url"] = url_auto(query, record["duration"])
                        self.insert_record(record, index+tracknumber-1)
        except Exception as e :
            self.tolog(f"Exception : {e}")

    def collect_playlist_spotify(self, url, auto_search=True, export_playlist=False, index=None) :
        if index==None :
            index = len(self.records)
        if url.count("open.spotify.com/playlist") == 1 or url.count("open.spotify.com/album") == 1:
            url = url.replace("open.spotify.com/", "open.spotify.com/embed/")
            url += "?utm_source=generator"
        json_sf = {}
        try :
            html_page = urllib.request.urlopen(url)
            html_content = html_page.read().decode()
            html_page.close()
            resource_html_quoted = re.findall("(?<=<script id=\"resource\" type=\"application/json\">\n)\s+([^<>]+)\n\s+(?=</script>)", html_content)
            resource_html_unquoted = urllib.parse.unquote(*resource_html_quoted)
            json_sf = json.loads(resource_html_unquoted)
        except Exception as e :
            self.tolog(f"Exception : {e}")
        if json_sf and isinstance(json_sf, dict) :
            if "name" in json_sf.keys() : 
                name_pls = json_sf["name"]
            else :
                name_pls = valid_filename(url)
            if export_playlist :
                try :
                    with open(valid_filename(f"Playlist Spotify - {name_pls}.json"), 'w', encoding='utf-8') as file :
                        json.dump(json_sf, file, indent=4)
                        self.tolog("Playlist exported")
                except Exception as e :
                    self.tolog(f"Exception : {e}")
            if "tracks" in json_sf and isinstance(json_sf["tracks"], dict) and "items" in json_sf["tracks"] and isinstance(json_sf["tracks"]["items"], list) :
                digits = max(2, len(str(len(json_sf["tracks"]["items"]))))
                tracknumber = 0
                for item in json_sf["tracks"]["items"] :
                    record = self.new_record()
                    tracknumber += 1
                    record["tracknumber"] = f"{tracknumber:0{digits}d}"
                    if isinstance(item, dict) and "track" in item.keys() and isinstance(item["track"], dict) and item["track"] :
                        if "name" in item["track"].keys() :
                            record["title"] = str(item["track"]["name"])
                        if "artists" in item["track"].keys() and isinstance(item["track"]["artists"], list) :
                            record["artist"] = ", ".join([str(el["name"]) if isinstance(el, dict) and "name" in el.keys() else "" for el in item["track"]["artists"]])
                        if "album" in item["track"].keys() and isinstance(item["track"]["album"], dict) and "name" in item["track"]["album"].keys() :
                            record["album"] = str(item["track"]["album"]["name"])
                        else :
                            record["album"] = name_pls
                        if "album" in item["track"].keys() and isinstance(item["track"]["album"], dict) and "release_date" in item["track"]["album"].keys() :
                            record["date"] = str(item["track"]["album"]["release_date"])
                        else :
                            if "release_date" in json_sf.keys() :                                
                                record["date"] = str(json_sf["release_date"])
                        if "duration_ms" in item["track"].keys() :
                            record["duration"] = int(item["track"]["duration_ms"])//1000
                    if  "album_type" in json_sf.keys() :
                        if "name" in item.keys() :
                            record["title"] = str(item["name"])
                        if "artists" in item.keys() and isinstance(item["artists"], list) :
                            record["artist"] = ", ".join([str(el["name"]) if isinstance(el, dict) and "name" in el.keys() else "" for el in item["artists"]])
                        if "name" in json_sf.keys()  :
                            record["album"] = str(json_sf["name"])
                        else :
                            record["album"] = name_pls
                        if "release_date" in json_sf.keys() :                                
                            record["date"] = str(json_sf["release_date"])
                        if "duration_ms" in item.keys() :
                            record["duration"] = int(item["duration_ms"])//1000
                    if "name" in json_sf.keys() and valid_filename(name_pls) :
                        record["folder"] = valid_filename(name_pls)
                    else :
                        record["folder"] = valid_filename(self.settings["folder_mask"].format(**record))
                    record["filename"] = valid_filename(self.settings["filename_mask"].format(**record))
                    if auto_search :
                        query = self.settings["query_mask"].format(**record)
                        self.tolog(f"Url auto query : {query}")
                        record["url"] = url_auto(query, record["duration"])
                    self.insert_record(record, index+tracknumber-1)
                    
    def track_renumbering(self):
        self.tolog(f"Tracks renumbering")
        digits = max(2, len(str(len(self.records))))
        for tracknumber, record in enumerate(self.records, start=1) :
            record["tracknumber"] = f"{tracknumber:0{digits}d}"

    def json_load(self, import_settings=False):
        self.tolog(f"Tracklist {self.settings['tracks_filename']}.json : load")
        try :
            with open(valid_filename(f"{self.settings['tracks_filename']}.json"), 'r', encoding='utf-8') as file:
                data = json.load(file)
                if import_settings and isinstance(data, dict) and "settings" in data.keys() :
                    for key in data["settings"].keys() :    # keep self.settings id
                        self.settings[key] = data["settings"][key]
                    self.tolog(f"Tracklist {self.settings['tracks_filename']}.json : getting settings")
                if isinstance(data, dict) and "records" in data.keys() :
                    data = data["records"]
                if isinstance(data, list) :
                    for item in data :
                        self.add_record(self.new_record(item))
        except Exception as e :
            self.tolog(f"Exception : {e}")

    def json_save(self, embed_settings = True):
        try :
            with open(valid_filename(f"{self.settings['tracks_filename']}.json"), 'w', encoding='utf-8') as file:
                if embed_settings :
                    data = {"records" : self.records, "settings" : self.settings}
                    json.dump(data, file, indent=4)
                else :
                    json.dump(self.records, file, indent=4)
                self.tolog(f"Tracklist saved as {self.settings['tracks_filename']}.json{f', settings embeded' if embed_settings else ''}")
        except Exception as e :
            self.tolog(f"Exception : {e}")
            
    def download(self, index=0, toend=True) :
        th = threading.Thread(target=self.download_launch, args=(index, toend))            
        th.start()
        
    def download_launch(self, index=0, toend=True) :
        if toend :
            try :
                max_dl = int(self.settings["max_dl"])
            except Exception as e :
                self.log(f"Exception : {e}\nmax_dl=20")
                max_dl = 20
            threads = {}
            for i, record in enumerate(self.records[index:], start=index) :
                threads[i] = threading.Thread(target=self.download_thread, args=(i, toend))
            ls_dl = [i for i in threads.keys()]
            while ls_dl  :
                while [threads[k].is_alive() for k in threads.keys()].count(True) < max_dl :
                    print([threads[k].is_alive() for k in threads.keys()].count(True))
                    i = ls_dl.pop(0)
                    th = threads[i]
                    th.start()
                    self.tolog(f"Starting thread : {i}")
                for i in ls_dl :
                    if threads[i].is_alive() :
                        threads[i].join()
        else :
            th = threading.Thread(target=self.download_thread, args=(index, toend))            
            th.start()
            
    def download_thread(self, index=0, toend=True) :
        downloads = [self.records[index]]   # list --> retry in case of 403
        num_folders = len(set([el['folder'] for el in self.records]))
        audioformat = self.settings["codec_chosen"]["codec"]
        ext = self.settings["codec_chosen"]["ext"]
        preferredquality = self.settings["codec_chosen"]["quality"]
        k = 0
        while downloads :
            k += 1
            record = downloads.pop(0)
            self.tolog(f"Start downloading : {record}")
            if "folder" in record.keys() and valid_filename(record["folder"]) :
                rep = valid_filename(record["folder"])
            else :
                rep = "tracks"
            try :
                self.tolog(f"Creating folder : {rep}")
                os.makedirs(rep, exist_ok=True)
            except Exception as e :
                self.tolog(f"Exception : {e}")
            if record["url"]=="auto" or record["url"]=="" :
                try :
                    query = self.settings['query_mask'].format(**record)
                    self.tolog(f"Url auto query : {query}")
                    url = url_auto(query)
                except Exception as e :
                    self.tolog(f"Exception : {e}")
            else :
                url = record["url"]
            if "filename" in record.keys() and valid_filename(record["filename"]) :
                filename = valid_filename(record["filename"])
            else :
                if valid_filename(self.settings["filename_mask"].format(**record)) :
                    filename = valid_filename(self.settings["filename_mask"].format(**record))
                else :
                    filename = str(k) 
            self.tolog(f"Preparing : {filename}.{ext} in {rep} ; quality : {preferredquality}")
            ydl_settings = {
                            'format': 'bestaudio/best',
                            'writethumbnail' : True,
                            'extractaudio': True,
                            'audioformat': audioformat,
                            'outtmpl': filename+'.%(ext)s',
                            'noplaylist': True,
                            'nocheckcertificate': True,
                            'proxy':"",
                            'quiet': False,
                            'addmetadata': True,
                            'logger' : self,
                            'postprocessors': [{
                                                'key': 'FFmpegExtractAudio',
                                                'preferredcodec': audioformat,
                                                'preferredquality': preferredquality,
                                                }, 
                                                {'key': 'EmbedThumbnail',}
                                                ]
                            }
            try :
                self.tolog(f"Downloading {filename}.{ext}")
                ydl = youtube_dl.YoutubeDL(ydl_settings)
                with ydl:
                    ydl.download([url])
            except Exception as e :
                self.tolog(f"Exception : {e}")
                if str(e)=="ERROR: unable to download video data: HTTP Error 403: Forbidden" :
                    self.tolog(f"Retry : {filename}.{ext}")
                    downloads.insert(0, record)
            try :
                self.tolog(f"Tagging {filename}.{ext}")
                if ext=="mp3" :
                    metatag = EasyID3(f"{filename}.{ext}")
                    for field in ["tracknumber", "title", "artist", "album", "date"] :
                        if record[field] :
                            metatag[field] = record[field]
                    metatag.save()
                if ext=="ogg" :
                    metatag = OggVorbis(f"{filename}.{ext}")
                    for field in ["tracknumber", "title", "artist", "album", "date"] :
                        if record[field] :
                            metatag[field.upper()] = record[field]
                    metatag.save()
                    pic = Picture()
                    with open(f"{filename}.jpg", "rb") as f:
                        pic.data = f.read()
                        pic.mime = u"image/jpeg"
                        pic.width = 500
                        pic.height = 500
                        pic.depth = 24 # color depth
                    metatag['metadata_block_picture']=[base64.b64encode(pic.write()).decode('ascii')]
                    metatag.save()
                if ext=="flac" :
                    metatag = FLAC(f"{filename}.{ext}")
                    for field in ["tracknumber", "title", "artist", "album", "date"] :
                        if record[field] :
                            metatag[field.upper()] = record[field]
                    metatag.save()
                    pic = Picture()
                    with open(f"{filename}.jpg", "rb") as f:
                        pic.data = f.read()
                        pic.mime = u"image/jpeg"
                        pic.width = 500
                        pic.height = 500
                        pic.depth = 16 # color depth
                    metatag.add_picture(pic)
                    metatag.save()
            except Exception as e :
                self.tolog(f"Exception : {e}")
            try :
                self.tolog(f"Moving {filename}.{ext} to {rep}/")
                os.rename(f"{filename}.{ext}", f"{rep}/{filename}.{ext}")
            except Exception as e :
                self.tolog(f"Exception : {e}")
            try :
                if not(self.settings["codec_chosen"]["EmbedThumbnail"]) :
                    if os.path.exists(f"{filename}.jpg") :
                        os.makedirs(f"{rep}/Covers", exist_ok=True)
                        os.rename(f"{filename}.jpg", f"{rep}/Covers/{filename}.jpg")
                        self.tolog(f"Moving {filename}.jpg to {rep}/Covers/")     
            except Exception as e :
                self.tolog(f"Exception : {e}")
        self.json_save()
        try :
            if num_folders == 1 :
                os.rename(f"{self.settings['tracks_filename']}.json", f"{rep}/tracks_{rep}.json")
                self.tolog(f"Moving {self.settings['tracks_filename']}.json to {rep}/")
            if num_folders > 1 :
                os.makedirs("tracks", exist_ok=True)
                os.rename(f"{self.settings['tracks_filename']}.json", f"tracks/{self.settings['tracks_filename']}.json")
                self.tolog(f"Moving {self.settings['tracks_filename']}.json to tracks/")
        except Exception as e :
            self.tolog(f"Exception : {e}")
        self.json_save()
        

                
def url_auto(query, duration=False) :
    query_string = urllib.parse.urlencode({"search_query" : query})
    if duration :
        if 0 < duration < 240 :
            query_string += "&sp=EgIYAQ%253D%253D"
        if 240 <= duration <= 1200 :
            query_string += "&sp=EgIYAw%253D%253D"
        if 1200 < duration :
            query_string += "&sp=EgIYAg%253D%253D"
    try :
        html_content = urllib.request.urlopen("https://www.youtube.com/results?"+query_string)
        search_results = re.findall(r'url\"\:\"\/watch\?v\=(.*?(?=\"))', html_content.read().decode())
        html_content.close()
    except Exception as e :
        print(e)
    if search_results :
        return "http://www.youtube.com/watch?v=" + search_results[0]
    else :
        return "Failed"
    

def valid_filename(st=""):
    st = st.replace('/', '-')
    return "".join(x for x in st if x.isalnum() or x in "._- ()[]")[:255]



class Gui(Playlist):
    def __init__(self) :    
        super().__init__()
        self.long = {
            "url" : 10,
            "tracknumber" : 4,
            "title" : 25,
            #"artist" : 20,
            #"album" : 20,
            "date" : 10,
            "folder" : 20,
            "filename" : 24
            }
        
        self.help = {
            "playlist_url" : "return : add playlist\nshift+return : add playlist and export original playlist",
            "tracks_filename" : "ctrl+l : load\nctrl+shift+l : load with settings\nctrl+s : save\nctrl+shift+s : save with settings",
            "query_mask" : "Youtube search in url field",
            "folder_mask" : "To apply in folder field",
            "filename_mask" : "To apply in filename field",
            "temp_mask" : "To apply in a field",
            "codec_chosen" : "",
            "max_dl" : "Number of simultaneous downloads",
            "url" : "return : open url with browser\nctrl+m : apply query mask",
            "tracknumber" : "ctrl+shift+r : renumbering from item",
            "title" : "ctrl+shift+backspace : delete line\nctrl+left|right : insert line before|after\nctrl+(shift)+up|down : insert playlist before|after (export)\nctrl+g : download item\nctrl+(shift)+g : download item (shift : from item to the end)\nctrl+(shift)+m : apply temp mask (from item to the end)",
            "artist" : "return : open wiki with browser\nctrl+shift+r : copy from item to the end\nctrl+(shift)+m : apply temp mask (from item to the end)",
            "album" : "ctrl+shift+r : copy from item to the end\nctrl+(shift)+m : apply temp mask (from item to the end)",
            "date" : "ctrl+shift+r : copy from item to the end\nctrl+(shift)+m : apply temp mask (from item to the end)",
            "filename" : "ctrl+(shift)+m : apply filename mask (from item to the end)",
            "folder" : "ctrl+shift+r : copy from item to the end\nctrl+(shift)+m : apply mask (from item to the end)",
            }
        self.root = tk.Tk()
        self.root.title("Youtube playlist downloader")
        self.root.focus_set()
        self.frame_settings = tk.Frame(self.root)
        self.frame_settings.grid(row=0, column=0)
        self.frame_settings.gui = self #access to records from record frame
        self.frame_settings.widgets = {}
        self.frame_metas = tk.Frame(self.root)
        self.frame_metas.gui = self #access to records from meta frame
        #self.frame_metas.grid(row=1, column=0)
        self.frame_metas.widgets = {}
        self.frame_records_container = tk.Frame(self.root)
        self.frame_records_container.grid(row=2, column=0)
        self.canvas = tk.Canvas(self.frame_records_container, width=1260, height=450)
        self.canvas.grid(row=0, column=0)
        self.frame_records = tk.Frame(self.canvas)
        self.canvas.create_window(0, 0, anchor="nw", window=self.frame_records)
        self.frame_records.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        #self.frame_records.grid(row=0, column=0)
        self.frame_records.gui = self #access to gui from record frame
        self.frame_records.widgets = {}
        self.scrollbar_y = tk.Scrollbar(self.frame_records_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        self.scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        self.scrollbar_x = tk.Scrollbar(self.frame_records_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar_x.grid(row=1, column=0, sticky=tk.EW)
        self.frame_settings.widgets[(0,0)] = Widget(self.frame_settings, wgt=tk.Label, text="Enter playlist url : \n (Youtube or Spotify)")
        self.frame_settings.widgets[(0,1)] = Widget(self.frame_settings, wgt=tk.Entry, dic=self.settings, key="playlist_url")
        self.frame_settings.widgets[(0,1)].w.bind('<Return>', lambda event : self.collect_playlist_gui(self.settings["playlist_url"], export_playlist=False))
        self.frame_settings.widgets[(0,1)].w.bind('<Shift-Return>', lambda event : self.collect_playlist_gui(self.settings["playlist_url"], export_playlist=True))
        self.frame_settings.widgets[(0,2)] = Widget(self.frame_settings, wgt=tk.Label, text=" or enter .json \n tracklist filename ")
        self.frame_settings.widgets[(0,3)] = Widget(self.frame_settings, wgt=tk.Entry, dic=self.settings, key="tracks_filename")
        self.frame_settings.widgets[(0,3)].w.bind('<Control-l>', lambda event : self.json_load_gui())
        self.frame_settings.widgets[(0,3)].w.bind('<Control-Shift-L>', lambda event : self.json_load_gui(import_settings=True))
        self.frame_settings.widgets[(0,3)].w.bind('<Control-s>', lambda event : self.json_save_gui())
        self.frame_settings.widgets[(0,3)].w.bind('<Control-Shift-S>', lambda event : self.json_save_gui(embed_settings=True))
        self.frame_settings.widgets[(0,4)] = Widget(self.frame_settings, wgt=tk.Label, dic=self.log, key="log", height=self.settings["log_lines"], width=65, bg='black', fg='green', justify=tk.LEFT, anchor='w') #, wraplength=400)
        #self.tolog = lambda st : self.frame_settings.widgets[(0,4)].stringvar.set("\n".join(f"{self.frame_settings.widgets[(0,4)].stringvar.get()}{st}".splitlines()[-self.settings["log_lines"]:]+"\n"))
        self.debug = self.tolog
        self.warning = self.tolog
        self.error = self.tolog
        for i, j in self.frame_settings.widgets.keys() :
            self.frame_settings.widgets[(i,j)].w.grid(row=i, column=j)
        
        self.frame_metas.widgets[(0,0)] = Widget(self.frame_metas, wgt=tk.Label, text="url auto search mask")
        self.frame_metas.widgets[(1,0)] = Widget(self.frame_metas, wgt=tk.Entry, dic=self.settings, key="query_mask")
        self.frame_metas.widgets[(0,1)] = Widget(self.frame_metas, wgt=tk.Label, text="temp mask")
        self.frame_metas.widgets[(1,1)] = Widget(self.frame_metas, wgt=tk.Entry, dic=self.settings, key="temp_mask")
        self.frame_metas.widgets[(0,2)] = Widget(self.frame_metas, wgt=tk.Label, text="folder mask")
        self.frame_metas.widgets[(1,2)] = Widget(self.frame_metas, wgt=tk.Entry, dic=self.settings, key="folder_mask")
        self.frame_metas.widgets[(0,3)] = Widget(self.frame_metas, wgt=tk.Label, text="filename mask")
        self.frame_metas.widgets[(1,3)] = Widget(self.frame_metas, wgt=tk.Entry, dic=self.settings, key="filename_mask")
        self.frame_metas.widgets[(0,4)] = Widget(self.frame_metas, wgt=tk.Label, text="codec")
        self.frame_metas.widgets[(1,4)] = Widget(self.frame_metas, wgt=ttk.Combobox, dic=self.settings, key="codec_chosen", ls=[el["name"] for el in self.CODECS], ls2=self.CODECS)
        self.frame_metas.widgets[(1,4)].stringvar.set(self.settings["codec_chosen"]["name"])
        self.frame_metas.widgets[(0,5)] = Widget(self.frame_metas, wgt=tk.Label, text="max simult. dl")
        self.frame_metas.widgets[(1,5)] = Widget(self.frame_metas, wgt=tk.Entry, dic=self.settings, key="max_dl")
        self.frame_metas.widgets[(1,5)].stringvar.set(self.settings["max_dl"])
        for i, j in self.frame_metas.widgets.keys() :
            self.frame_metas.widgets[(i,j)].w.grid(row=i, column=j)
        self.root.mainloop()

    def tolog(self, st) :
        print(st)
        self.frame_settings.widgets[(0,4)].stringvar.set("\n".join(f"{self.frame_settings.widgets[(0,4)].stringvar.get()}{st}".splitlines()[-self.settings["log_lines"]:])+"\n")

    def show_metas(self):
        self.frame_metas.grid(row=1, column=0)
    
    def update_records(self):
        for w in self.frame_records.widgets.values() :
            w.widget_del()
        self.frame_records.widgets = {}
        self.frame_records.widgets[(0,0)] = Widget(self.frame_records, wgt=tk.Label, text="id")
        self.frame_records.widgets[(0,0)].w.grid(row=0, column=0)
        FIELDS = [el["name"] for el in self.FIELDS if el["type"]!="hidden"]
        for j, field in enumerate(FIELDS, start=1) :
            self.frame_records.widgets[(0,j)] = Widget(self.frame_records, wgt=tk.Label, text="tnbr" if field=="tracknumber" else field)
            self.frame_records.widgets[(0,j)].w.grid(row=0, column=j)            
        for i, record in enumerate(self.records, start=1) :
            self.frame_records.widgets[(i,0)] = Widget(self.frame_records, wgt=tk.Label, text=str(i-1))
            self.frame_records.widgets[(i,0)].w.grid(row=i, column=0)
            for j, key in enumerate(FIELDS, start=1) :
                if key in self.long.keys() :
                    self.frame_records.widgets[(i,j)] = Widget(self.frame_records, wgt=tk.Entry, dic=record, key=key, index=i-1, width=self.long[key])
                else :
                    self.frame_records.widgets[(i,j)] = Widget(self.frame_records, wgt=tk.Entry, dic=record, key=key, index=i-1)
                self.frame_records.widgets[(i,j)].w.grid(row=i, column=j)
        
    def update_metas(self):
        for W in self.frame_metas.widgets.values() :
            if W.wgt==tk.Entry :
                W.stringvar.set(W.dic[W.key])
        
    def collect_playlist_gui(self, url, export_playlist=False, index=None):
        th = threading.Thread(target=self.collect_playlist_thread, args=(url, export_playlist,index))
        th.start()
        
    def collect_playlist_thread(self, url, export_playlist=False, index=None):
        self.collect_playlist(url, export_playlist=export_playlist, index=index)
        self.show_metas()
        self.update_records()
    
    def json_load_gui(self, import_settings=False):
        self.json_load(import_settings)
        self.update_metas()
        self.show_metas()
        self.update_records()
        
    def json_save_gui(self, embed_settings=False):
        self.json_save(embed_settings)
        

class Widget():      
    def __init__(self, frame, wgt=None, dic=None, key=None, ls=None, ls2=None, text=None, index=0, **args):
        self.frame = frame
        self.wgt = wgt
        self.dic = dic
        self.key = key
        self.ls  = ls
        self.ls2  = ls2
        self.index = index
        if text==None :
            self.stringvar = tk.StringVar(value=self.dic[self.key])
        else :
            self.stringvar = tk.StringVar(value=text)
        if wgt == tk.Entry :
            self.cache = self.stringvar.get()
            self.stringvar.trace_add('write', self.updating_from_entry())
            self.w = wgt(self.frame, textvariable=self.stringvar, validate='key', **args)    
            self.w.bind('<FocusIn>', lambda event : self.cache_in())
            self.w.bind('<Control-z>', lambda event : self.undo())
            if self.key in [el["name"] for el in Playlist.FIELDS] :
                self.w.bind('<Control-Shift-BackSpace>', lambda event : self.del_record())
                self.w.bind('<Control-Left>', lambda event : self.insert_record_before())
                self.w.bind('<Control-Right>', lambda event : self.insert_record_after())
                self.w.bind('<Control-Up>', lambda event : self.insert_playlist_before())
                self.w.bind('<Control-Shift-Up>', lambda event : self.insert_playlist_before(export_playlist=True))
                self.w.bind('<Control-Down>', lambda event : self.insert_playlist_after()) 
                self.w.bind('<Control-Shift-Down>', lambda event : self.insert_playlist_after(export_playlist=True))
                self.w.bind('<Control-g>', lambda event : self.frame.gui.download(index=self.index, toend=False))
                self.w.bind('<Control-Shift-G>', lambda event : self.frame.gui.download(index=self.index, toend=True))
            if (self.key, True) in [(field["name"], field["copy"]) for field in Playlist.FIELDS] :
                self.w.bind('<Control-Shift-R>', lambda event : self.replace_all())
            if self.key=="tracknumber" :
                self.w.bind('<Control-Shift-R>', lambda event : self.tracks_renumbering())
            if self.key in ["title", "artist", "album", "date", "folder", "filename"] :
                self.w.bind('<Control-m>', lambda event : self.replace_from_mask())
                self.w.bind('<Control-Shift-M>', lambda event : self.replace_all_from_mask())
            if self.key=="url" :
                self.w.bind('<Return>', lambda event : self.browse_url())
                self.w.bind('<Control-m>', lambda event : self.auto_query())
            if self.key=="artist" :
                self.w.bind('<Return>', lambda event : self.wiki())                
        if wgt == tk.Label :
            self.w = wgt(self.frame, textvariable=self.stringvar, **args)
        #if wgt == tk.Button :
        #    self.w = wgt(self.frame, textvariable=self.stringvar, command=self.help, **args)
        if wgt == ttk.Combobox :
            self.w = ttk.Combobox(self.frame, textvariable=self.stringvar, values=self.ls, state="readonly", **args)
            self.w.bind('<<ComboboxSelected>>', lambda event : self.updating_from_combo())
    
    def updating_from_entry(self) :
        def f(*args) :
            self.dic[self.key] = self.stringvar.get()
        return f
    
    def updating_from_combo(self) :
        self.dic[self.key] = self.ls2[self.w.current()]
        self.stringvar.set(self.ls2[self.w.current()]["name"])
        self.frame.gui.tolog(f"Selected : {self.ls2[self.w.current()]['name']}")
    
    def browse_url(self) :
        webbrowser.open_new_tab(self.dic["url"])
    
    def wiki(self) :
        webbrowser.open_new_tab(f"https://fr.wikipedia.org/w/index.php?search=\"{self.dic['artist']}\"")
 
    def widget_del(self):
        self.w.grid_forget()
        del self.stringvar
        self.w.destroy()
        del self
    
    def cache_in(self):
        self.cache = self.stringvar.get()
        self.help()
    
    def undo(self):
        cache = self.cache
        self.cache = self.stringvar.get()
        self.stringvar.set(cache)
            
    def replace_all(self):
        for w in self.frame.widgets.values() :
            if w.key == self.key and w.wgt == tk.Entry and w.index>=self.index :
                w.stringvar.set(self.stringvar.get())
    
    def tracks_renumbering(self):
        digits = max(2, len(str(len(self.frame.gui.records))))
        tracknumber = 1 
        for w in self.frame.widgets.values() :
            if w.key=="tracknumber" and w.index>=self.index :
                w.stringvar.set(f"{tracknumber:0{digits}d}")
                tracknumber += 1
                
    def replace_from_mask(self):
        try :
            if self.key in ["folder", "filename"] :
                self.stringvar.set(valid_filename(self.frame.gui.settings[f"{self.key}_mask"].format(**self.dic)))
            else :
                self.stringvar.set(self.frame.gui.settings["temp_mask"].format(**self.dic))
        except Exception as e :
            self.frame.gui.tolog(f"Exception : {e}")    

    def replace_all_from_mask(self):
        for w in self.frame.widgets.values() :
            if w.key == self.key and w.wgt == tk.Entry and w.index>=self.index :
                try :
                    if self.key in ["folder", "filename"] :
                        w.stringvar.set(valid_filename(self.frame.gui.settings[f"{self.key}_mask"].format(**w.dic)))
                    else :
                        w.stringvar.set(self.frame.gui.settings["temp_mask"].format(**w.dic))
                except Exception as e :
                    self.frame.gui.tolog(f"Exception : {e}")
    
    def auto_query(self):
        self.stringvar.set(url_auto(self.frame.gui.settings["query_mask"].format(**self.dic), duration=self.dic["duration"]))
        self.frame.gui.tolog(f"Query : {self.frame.gui.settings['query_mask'].format(**self.dic)}")
        record = {}
        try :
            ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s', 'quiet':False, 'logger':self.frame.gui})
            with ydl :
                item = ydl.extract_info(self.stringvar.get(), download=False)
                if "track" in item.keys() : 
                    record["title"] = item["track"]
                if "title" in item.keys() : 
                    record["title"] = item["title"]
                if "uploader" in item.keys() :
                    record["artist"] = item["uploader"]
                if "artist" in item.keys() : 
                    record["artist"] = item["artist"]
                if "playlist" in item.keys() : 
                    record["album"] = item["playlist"]
                if "album" in item.keys() :
                    record["album"] = item["album"]
                if "release_year" in item.keys() : 
                    record["date"] = str(item["release_year"])
                record["tracknumber"] = "01"
                record["folder"] = valid_filename(self.frame.gui.settings["folder_mask"].format(**record))                    
                record["filename"] = valid_filename(self.frame.gui.settings["filename_mask"].format(**record))
        except Exception as e :
            self.frame.gui.tolog(f"Exception : {e}")
        for w in self.frame.widgets.values() :
            if w.index==self.index and w.wgt==tk.Entry and w.key!="url" and not(self.dic[w.key]) and w.key in record.keys() and record[w.key] :
                w.stringvar.set(record[w.key])
                
                                            
        
                    
    def del_record(self):
        self.frame.gui.tolog(f"Erasing at {self.index} : {self.dic}")
        self.frame.gui.records.pop(self.index)
        self.frame.gui.update_records()
    
    def insert_record_before(self):
        self.frame.gui.insert_record(self.frame.gui.new_record(), self.index)
        self.frame.gui.update_records()

    def insert_record_after(self):
        self.frame.gui.insert_record(self.frame.gui.new_record(), self.index+1)
        self.frame.gui.update_records()
        
    def insert_playlist_before(self, export_playlist=False):
        self.frame.gui.collect_playlist_gui(url=self.frame.gui.settings["playlist_url"], export_playlist=export_playlist, index=self.index)
        self.frame.gui.update_records()

    def insert_playlist_after(self, export_playlist=False):
        self.frame.gui.collect_playlist_gui(url=self.frame.gui.settings["playlist_url"], export_playlist=export_playlist, index=self.index+1)
        self.frame.gui.update_records()
        
    def help(self):
        self.frame.gui.tolog(f"\nHELP : {self.key}\n{self.frame.gui.help[self.key]}")
        if self.key=="folder" :
            self.frame.gui.tolog(f"\nINFO : How many folders ? {len(set([el['folder'] for el in self.frame.gui.records]))}")
        if self.key=="filename" :
            self.frame.gui.tolog(f"\nINFO : no names conflict, ok" if len([(el["folder"], el["filename"]) for el in self.frame.gui.records])==len(set([(el["folder"], el["filename"]) for el in self.frame.gui.records])) else "\nWARNING : duplicate names !")
   

if __name__ == "__main__" :
    gui=Gui()