import os
from queue import Queue
from time import sleep
import signal

from bottle import Bottle
from bottle import request
from bottle import static_file
import youtube_dl

from youtube_dl_server.utils import StoppableThread

app = Bottle()

ROOT = os.path.join(os.path.dirname(__file__), 'static')


@app.route('/')
def index():
    return static_file('index.html', root=ROOT)


@app.route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=ROOT)


@app.route('/status', method='GET')
def q():
    return {
        "success" : True,
        "status": app.status,
    }


@app.route('/q', method='GET')
def q():
    return {
        "success" : True,
        "q": list(app.queue.queue),
    }


@app.route('/q', method='POST')
def q_put():
    url = request.forms.get( "url" )
    if url:
        app.queue.put(url)
        print("Added url " + url + " to the download queue")
        return {"success": True, "url": url }
    else:
        return {"success": False, "error": "dl called without a url" }


class YTWorker(StoppableThread):
    def run(self):
        print("Started download thread")
        while not self.stopped():
            url = app.queue.get()
            self.download(url)
            app.queue.task_done()

    def download(self, url):
        ydl_opts = {
            'progress_hooks': [my_hook],
            'call_home': False,
            'outtmpl': "/downloads/%(title)s.%(ext)s",
            'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
            'writethumbnail': True,
            'cachedir': '/tmp',
            'merge_output_format': 'mp4',
        }
        print("Starting download of " + url)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])


def my_hook(d):
    name = d['filename']
    app.status[name] = d
    status = d['status']
    if status == 'finished':
        print("Finished: {}".format(name))


def run():
    global done
    app.queue = Queue()
    app.status = {}

    worker = YTWorker(daemon=True)
    worker.start()
    app.run(host='0.0.0.0', port=8080, debug=True)
    worker.stop()


if __name__ == "__main__":
    def handler(*args):
        app.close()
    signal.signal(signal.SIGINT, handler)
    run()
