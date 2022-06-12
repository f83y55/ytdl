import os
import json

MAINROOT = "."
COPY = True
if COPY :
    BASE = "000BASE"
    BASE_ARTISTS = "ARTISTS_ONLY"
    BASE_ALBUMS = "ALBUMS_ONLY"
    try :
        os.makedirs(os.path.join(MAINROOT, BASE), exist_ok=True)
        os.makedirs(os.path.join(MAINROOT, BASE, BASE_ARTISTS) , exist_ok=True)
        os.makedirs(os.path.join(MAINROOT, BASE, BASE_ALBUMS), exist_ok=True)
    except Exception as e :
        print(f"Exception : {e}")


def json_load(filename):
    #print(f"      Tracklist {filename} : load")
    try :
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, dict) and "records" in data.keys() :
                return data["records"]
            if isinstance(data, list) :
                return data
            else :
                print(f"      ERROR : {filename}")
    except Exception as e :
        print(f"Exception : {e}")

def json_save(filename, records=[]):
    try :
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(records, file, indent=4)
            #print(f"    Tracklist saved as {filename}")
    except Exception as e :
        print(f"Exception : {e}")
 
if __name__ == "__main__" :
    artists = [element for element in os.listdir(MAINROOT) if os.path.isdir(element)]
    if COPY :
        artists.remove(BASE)
    for artist in artists :
        print(f"  Artist : {artist}")
        albums = [element for element in os.listdir(os.path.join(MAINROOT, artist)) if os.path.isdir(os.path.join(MAINROOT, artist, element))]
        records = []   # artist compilation
        for album in albums :
            print(f"    Album : {album}")
            jsons = [element for element in os.listdir(os.path.join(MAINROOT, artist, album)) if element.endswith(".json")]
            if jsons :
                if len(jsons)>1 :
                    print(f"      WARNING : more than 1 tracklist json file !")
                    for k, json_file in enumerate(jsons) :
                        print(f"        k = {k} ; file = {json_file}")
                    k = int(input(f"        enter k to select a file : "))
                    json_file = jsons[k]
                else :
                    json_file = jsons[0]
                record = json_load(os.path.join(MAINROOT, artist, album, json_file))
                if COPY :
                    json_save(os.path.join(MAINROOT, BASE, BASE_ALBUMS, f"tracks_{album}.json"), record)
                records.extend(record)
            else :
                print(f"      WARNING : No tracklist json file ! => pass.")
        if records :
            json_save(os.path.join(MAINROOT, artist, f"tracks_{artist}.json"), records)
            if COPY :
                json_save(os.path.join(MAINROOT, BASE, BASE_ARTISTS, f"tracks_{artist}.json"), records)




