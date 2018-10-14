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
    return {
        "success": True,
        "state": {
            "https://www.youtube.com/watch?v=F2bKVEVUOPg": {
                "status": "analysing",
                "title": "https://www.youtube.com/watch?v=F2bKVEVUOPg"
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
