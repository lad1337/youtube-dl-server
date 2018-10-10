from threading import Thread
from queue import Queue

from bottle import Bottle
from bottle import request
from bottle import static_file
import youtube_dl

app = Bottle()


@app.route('/youtube-dl')
def dl_queue_list():
    return static_file('index.html', root='./')


@app.route('/youtube-dl/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/youtube-dl/q', method='GET')
def q():
    return {
        "success" : True,
        "q": list(app.queue.queue),
    }


@app.route('/youtube-dl/status', method='GET')
def q():
    return {
        "success" : True,
        "status": app.status,
    }


@app.route('/youtube-dl/q', method='POST')
def q_put():
    url = request.forms.get( "url" )
    if url:
        app.queue.put(url)
        print("Added url " + url + " to the download queue")
        return {"success": True, "url": url }
    else:
        return {"success": False, "error": "dl called without a url" }


def dl_worker():
    while not done:
        item = app.queue.get()
        download(item)
        app.queue.task_done()


class YTDLLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    name = d['filename']
    app.status[name] = d
    status = d['status']
    if status == 'finished':
        print("Finished: {}".format(name))


def download(url):
    ydl_opts = {
        'logger': YTDLLogger(),
        'progress_hooks': [my_hook],
        'call_home': False,
        'outtmpl': "youtube-dl/%(title)s.%(ext)s",
        #'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
        'writethumbnail': True,
        'cachedir': '/tmp',
        'merge_output_format': 'mp4',
    }
    print("Starting download of " + url)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    old = [
        "youtube-dl",
        "-o",
        "/youtube-dl/.incomplete/%(title)s.%(ext)s",
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
        "--exec",
        "touch {} && mv {} /youtube-dl/",
        "--merge-output-format",
        "mp4",
        url,
    ]

if __name__ == "__main__":
    app.queue = Queue()
    app.status = {}
    done = False
    dl_thread = Thread(target=dl_worker)
    dl_thread.start()
    print("Started download thread")
    app.run(host='0.0.0.0', port=8080, debug=True)
    done = True
    dl_thread.join()
