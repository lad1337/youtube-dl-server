import os
from multiprocessing import JoinableQueue
from multiprocessing import Manager
import signal

from bottle import Bottle
from bottle import request
from bottle import static_file

from youtube_dl_server.youtube import Task
from youtube_dl_server.youtube import YTWorker

ROOT = os.path.join(os.path.dirname(__file__), 'static')


class Server(Bottle):
    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
        self._manager = Manager()
        self.state = self._manager.dict()
        self.workers = []
        self.queue = JoinableQueue()

    def spawn_n_workers(self, n, **kwargs):
        for _ in range(n):
            worker = YTWorker(queue=self.queue, state=self.state, **kwargs)
            worker.start()
            self.workers.append(worker)

    def run(self, n_workers=5, **kwargs):
        self.spawn_n_workers(n_workers)
        self.spawn_n_workers(1, download=False)
        super(Server, self).run(**kwargs)

    def close(self):
        for w in self.workers:
            w.join()
        super(Server, self).close()


app = Server()


@app.route('/')
def index():
    return static_file('index.html', root=ROOT)


@app.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=ROOT)


@app.route('/state', method='GET')
def state():
    return {
        "success" : True,
        "state": dict(app.state),
    }
    # for testing the ui ... for now
    import random
    return {
        "success": True,
        "state": {
            "https://www.youtube.com/watch?v=F2bKVEVUOPg": {
                "status": "analysing",
                "title": "https://www.youtube.com/watch?v=F2bKVEVUOPg",
                "thumbnail": "",
            },
            "https://www.youtube.com/watch?v=sB_cM6rT3hM": {
                "_elapsed_str": "00:06",
                "_eta_str": "00:00",
                "_percent_str": "100.0%",
                "_speed_str": " 6.57MiB/s",
                "_total_bytes_str": "461.98MiB",
                "abr": 160,
                "acodec": "opus",
                "age_limit": 0,
                "alt_title": None,
                "annotations": None,
                "artist": None,
                "automatic_captions": {},
                "average_rating": 4.89880275726,
                "categories": [
                    "Film & Animation"
                ],
                "channel_id": "UCzH3iADRIq1IJlIXjfNgTpA",
                "channel_url": "http://www.youtube.com/channel/UCzH3iADRIq1IJlIXjfNgTpA",
                "chapters": None,
                "creator": None,
                "description": "If housekeeping walks in on you naked in your hotel room listening to music you clearly have one and only one option...JUST DANCE! This episode originally aired on October 3, 2016 and is sponsored by Dollar Shave Club (http://bit.ly/2ermjer) and Lyft (http://lft.to/2f9dGp6)\n\n» Join FIRST to watch episodes early: http://bit.ly/2vbk36i\n» Get your Rooster Teeth merch: http://bit.ly/2hhhTfN\n» Subscribe: http://bit.ly/13y3Gum\n\nAbout On The Spot:\nRooster Teeth's official game show! A live half hour of fast-paced laughs as host Jon Risinger puts two RT teams on the spot for points and mayhem.\n\nMore Rooster Teeth:\n» Achievement Hunter: http://bit.ly/AHYTChannel\n» Let's Play: http://bit.ly/1BuRgl1\n» Red vs. Blue: http://bit.ly/RvBChannel\n\nOn The Spot: Ep. 73 - Hotel Room Fiasco! | Rooster Teeth\nhttps://www.youtube.com/user/RoosterTeeth",
                "dislike_count": 131,
                "display_id": "sB_cM6rT3hM",
                "downloaded_bytes": 33026779,
                "duration": 2079,
                "elapsed": 6.810099840164185,
                "end_time": None,
                "episode": "Episode 5",
                "episode_number": 5,
                "eta": 0,
                "ext": "webm",
                "extractor": "youtube",
                "extractor_key": "Youtube",
                "filename": "downloads/On The Spot - Ep. 73 - Hotel Room Fiasco! _ Rooster Teeth.f140.m4a",
                "format": "248 - 1920x1080 (1080p)+251 - audio only (DASH audio)",
                "format_id": "248+251",
                "fps": 30,
                "height": 1080,
                "id": "sB_cM6rT3hM",
                "is_live": None,
                "license": None,
                "like_count": 5047,
                "n_entries": 12,
                "playlist": "On The Spot - Season 7",
                "playlist_id": "PLUBVPK8x-XMiEp4dyPYOfSyoyAAdC3T8k",
                "playlist_index": 5,
                "playlist_title": "On The Spot - Season 7",
                "playlist_uploader": "Rooster Teeth",
                "playlist_uploader_id": "RoosterTeeth",
                "requested_subtitles": None,
                "resolution": None,
                "season": "Season 7",
                "season_number": 7,
                "series": "On the Spot",
                "speed": 6891204.184403016,
                "start_time": None,
                "status": "finished",
                "stretched_ratio": None,
                "subtitles": {},
                "thumbnail": "https://i.ytimg.com/vi/sB_cM6rT3hM/maxresdefault.jpg",
                "thumbnails": [
                    {
                        "id": "0",
                        "url": "https://i.ytimg.com/vi/sB_cM6rT3hM/maxresdefault.jpg"
                    }
                ],
                "title": "On The Spot: Ep. 73 - Hotel Room Fiasco! | Rooster Teeth",
                "tmpfilename": "downloads/On The Spot - Ep. 73 - Hotel Room Fiasco! _ Rooster Teeth.f140.m4a.part",
                "total_bytes": 33026779,
                "track": None,
                "updated_at": 1539533533.612248,
                "upload_date": "20161105",
                "uploader": "Rooster Teeth",
                "uploader_id": "RoosterTeeth",
                "uploader_url": "http://www.youtube.com/user/RoosterTeeth",
                "vbr": None,
                "vcodec": "vp9",
                "view_count": 283556,
                "webpage_url": "https://www.youtube.com/watch?v=sB_cM6rT3hM",
                "webpage_url_basename": "sB_cM6rT3hM",
                "width": 1920
            },
            "https://www.youtube.com/watch?v=rtrN4sRT0yE": {
                "_eta_str": "00:06",
                "_percent_str": " {}.0%".format(random.randint(1, 99)),
                "_speed_str": " 2.35MiB/s",
                "_total_bytes_str": "551.94MiB",
                "abr": 160,
                "acodec": "opus",
                "age_limit": 0,
                "alt_title": None,
                "annotations": None,
                "artist": None,
                "automatic_captions": {},
                "average_rating": 4.93473386765,
                "categories": [
                    "Film & Animation"
                ],
                "channel_id": "UCzH3iADRIq1IJlIXjfNgTpA",
                "channel_url": "http://www.youtube.com/channel/UCzH3iADRIq1IJlIXjfNgTpA",
                "chapters": None,
                "creator": None,
                "description": "When is Hanukkah? Why 8 candles and not 7? Why do the Jews keep stealing my geese? All good questions for your local rabbi. This episode originally aired December 22, 2016 and is sponsored by Lyft http://lft.to/2f9dGp6 and Trunk Club http://bit.ly/2930z9x\n\n» Join FIRST to watch episodes early: http://bit.ly/2vbk36i\n» Get your Rooster Teeth merch: http://bit.ly/2hhhTfN\n» Subscribe: http://bit.ly/13y3Gum\n\nAbout On The Spot:\nRooster Teeth's official game show! A live half hour of fast-paced laughs as host Jon Risinger puts two RT teams on the spot for points and mayhem.\n\nMore Rooster Teeth:\n» Achievement Hunter: http://bit.ly/AHYTChannel\n» Let's Play: http://bit.ly/1BuRgl1\n» Red vs. Blue: http://bit.ly/RvBChannel\n\nOn The Spot: Ep. 80 - Rabbi Burnie Burns | Rooster Teeth\nhttps://www.youtube.com/user/RoosterTeeth",
                "dislike_count": 167,
                "display_id": "rtrN4sRT0yE",
                "downloaded_bytes": 562414542,
                "duration": 2636,
                "elapsed": 127.38903999328613,
                "end_time": None,
                "episode": "Episode 12",
                "episode_number": 12,
                "eta": 6,
                "ext": "mp4",
                "extractor": "youtube",
                "extractor_key": "Youtube",
                "filename": "downloads/On The Spot - Ep. 80 - Rabbi Burnie Burns _ Rooster Teeth.f137.mp4",
                "format": "137 - 1920x1080 (1080p)+251 - audio only (DASH audio)",
                "format_id": "137+251",
                "fps": 30,
                "height": 1080,
                "id": "rtrN4sRT0yE",
                "is_live": None,
                "license": None,
                "like_count": 10068,
                "n_entries": 12,
                "playlist": "On The Spot - Season 7",
                "playlist_id": "PLUBVPK8x-XMiEp4dyPYOfSyoyAAdC3T8k",
                "playlist_index": 12,
                "playlist_title": "On The Spot - Season 7",
                "playlist_uploader": "Rooster Teeth",
                "playlist_uploader_id": "RoosterTeeth",
                "requested_subtitles": None,
                "resolution": None,
                "season": "Season 7",
                "season_number": 7,
                "series": "On the Spot",
                "speed": 2465232.8238326223,
                "start_time": None,
                "status": "downloading",
                "stretched_ratio": None,
                "subtitles": {},
                "thumbnail": "https://i.ytimg.com/vi/rtrN4sRT0yE/maxresdefault.jpg",
                "thumbnails": [
                    {
                        "id": "0",
                        "url": "https://i.ytimg.com/vi/rtrN4sRT0yE/maxresdefault.jpg"
                    }
                ],
                "title": "On The Spot: Ep. 80 - Rabbi Burnie Burns | Rooster Teeth foo bar baz tralllllaa asd",
                "tmpfilename": "downloads/On The Spot - Ep. 80 - Rabbi Burnie Burns _ Rooster Teeth.f137.mp4.part",
                "total_bytes": 578754886,
                "track": None,
                "updated_at": 1539533866.978368,
                "upload_date": "20161224",
                "uploader": "Rooster Teeth",
                "uploader_id": "RoosterTeeth",
                "uploader_url": "http://www.youtube.com/user/RoosterTeeth",
                "vbr": None,
                "vcodec": "avc1.640028",
                "view_count": 515754,
                "webpage_url": "https://www.youtube.com/watch?v=rtrN4sRT0yE",
                "webpage_url_basename": "rtrN4sRT0yE",
                "width": 1920
            },
            "https://www.youtube.com/watch?v=3-FBUSCCpGU": {
                "abr": 128,
                "acodec": "mp4a.40.2",
                "age_limit": 0,
                "alt_title": None,
                "annotations": None,
                "artist": None,
                "automatic_captions": {},
                "average_rating": 4.92978620529,
                "categories": [
                    "Gaming"
                ],
                "channel_id": "UCzH3iADRIq1IJlIXjfNgTpA",
                "channel_url": "http://www.youtube.com/channel/UCzH3iADRIq1IJlIXjfNgTpA",
                "chapters": None,
                "creator": None,
                "description": "Jack and Joel take on Ray and Ryan on the return of On The Spot, sponsored by NatureBox(http://bit.ly/1AxXTa0).\n\n» Join FIRST to watch episodes early: http://bit.ly/2vbk36i\n» Get your Rooster Teeth merch: http://bit.ly/2hhhTfN\n» Subscribe: http://bit.ly/13y3Gum\n\nAbout On The Spot:\nRooster Teeth's official game show! A live half hour of fast-paced laughs as host Jon Risinger puts two RT teams on the spot for points and mayhem.\n\nMore Rooster Teeth:\n» Achievement Hunter: http://bit.ly/AHYTChannel\n» Let's Play: http://bit.ly/1BuRgl1\n» Red vs. Blue: http://bit.ly/RvBChannel\n\nOn The Spot: Ep. 11 | Rooster Teeth\nhttps://www.youtube.com/user/RoosterTeeth",
                "dislike_count": 192,
                "display_id": "3-FBUSCCpGU",
                "downloaded_bytes": 127206664,
                "duration": 2262,
                "elapsed": 115.95673489570618,
                "end_time": None,
                "episode": "Episode 1",
                "episode_number": 1,
                "eta": 123,
                "ext": "mp4",
                "extractor": "youtube",
                "extractor_key": "Youtube",
                "filename": "downloads/On The Spot - Ep. 11 _ Rooster Teeth.f136.mp4",
                "format": "136 - 1280x720 (720p)+140 - audio only (DASH audio)",
                "format_id": "136+140",
                "fps": 30,
                "height": 720,
                "id": "3-FBUSCCpGU",
                "is_live": None,
                "license": None,
                "like_count": 10746,
                "n_entries": 10,
                "playlist": "On the Spot - Season 2",
                "playlist_id": "PLUBVPK8x-XMjCW_dxkbT4ZxAJq65gzOJq",
                "playlist_index": 1,
                "playlist_title": "On the Spot - Season 2",
                "playlist_uploader": "Rooster Teeth",
                "playlist_uploader_id": "RoosterTeeth",
                "requested_subtitles": None,
                "resolution": None,
                "season": "Season 2",
                "season_number": 2,
                "series": "On the Spot",
                "speed": 1303513.0644555578,
                "start_time": None,
                "status": "",
                "stretched_ratio": None,
                "subtitles": {},
                "thumbnail": "https://i.ytimg.com/vi/3-FBUSCCpGU/maxresdefault.jpg",
                "thumbnails": [
                    {
                        "id": "0",
                        "url": "https://i.ytimg.com/vi/3-FBUSCCpGU/maxresdefault.jpg"
                    }
                ],
                "title": "On The Spot: Ep. 11 | Rooster Teeth",
                "tmpfilename": "downloads/On The Spot - Ep. 11 _ Rooster Teeth.f136.mp4.part",
                "total_bytes": 288206682,
                "track": None,
                "upload_date": "20150213",
                "uploader": "Rooster Teeth",
                "uploader_id": "RoosterTeeth",
                "uploader_url": "http://www.youtube.com/user/RoosterTeeth",
                "vbr": None,
                "vcodec": "avc1.4d401f",
                "view_count": 541337,
                "webpage_url": "https://www.youtube.com/watch?v=3-FBUSCCpGU",
                "webpage_url_basename": "3-FBUSCCpGU",
                "width": 1280
            }
        }
    }


@app.route('/q', method='POST')
def q_put():
    url = request.forms.get( "url" )
    if url:
        app.queue.put(Task(url))
        print("Added url " + url + " to the download queue")
        return {"success": True, "url": url }
    else:
        return {"success": False, "error": "dl called without a url" }


def run():
    app.run(host='0.0.0.0', port=8080, debug=True)


if __name__ == "__main__":
    def handler(*args):
        app.close()
    signal.signal(signal.SIGINT, handler)
    run()
