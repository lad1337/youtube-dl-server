from datetime import datetime

import youtube_dl as ydl
from youtube_dl.utils import UnavailableVideoError
from youtube_dl import YoutubeDL as YoutubeDL_

from multiprocessing import Process

DEFAULT_TEMPLATE = "%(title)s.%(ext)s"

class YoutubeDL(YoutubeDL_):
    def download(self, url_list):
        """Download a given list of URLs."""
        outtmpl = self.params.get('outtmpl', ydl.DEFAULT_OUTTMPL)
        if (len(url_list) > 1 and
                outtmpl != '-' and
                '%' not in outtmpl and
                self.params.get('max_downloads') != 1):
            raise ydl.SameFileError(outtmpl)

        out = []
        for url in url_list:
            try:
                # It also downloads the videos
                res = self.extract_info(
                    url, force_generic_extractor=self.params.get('force_generic_extractor', False))
            except UnavailableVideoError:
                self.report_error('unable to download video')
            except ydl.MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloaded files reached.')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    out.append(res)

        return out


class Task:

    def __init__(self, url, info=None):
        self.url = url
        self.info = info or {}

    @property
    def is_playlist(self):
        return 'playlist' in self.url

    @property
    def investigate(self):
        return not self.info

    @classmethod
    def from_info(cls, info):
        return cls(info['webpage_url'], info=info)


class YTWorker(Process):

    def __init__(self, queue, state, template=DEFAULT_TEMPLATE ,download=True, *args, **kwargs):
        super(YTWorker, self).__init__(*args, **kwargs)
        self.queue = queue
        self.state = state
        self.should_download = download
        self.out_template = template
        self._url = None

    def __str__(self):
        s = super(YTWorker, self).__str__()
        type_ = "downloader" if self.should_download else "info getter"
        return "{} {}".format(s, type_)

    def run(self):
        print("Started {}".format(self))
        while True:
            task = self.queue.get()
            if task.investigate:
                entries = self.get_info(task)
                for info in entries:
                    t = Task.from_info(info)
                    self.inform(task=t)
                    self.queue.put(t)
            elif self.should_download:
                self.download(task)
            else:
                self.queue.put(task)
            self.queue.task_done()

    def inform(self, item=None, task=None):
        def maybe_remove(d, *keys):
            for key in keys:
                try:
                    del item[key]
                except KeyError:
                    pass

        if task is not None:
            self._url = task.url
            item = task.info
        item['updated_at'] = datetime.now().timestamp()
        print("Inform {s._url} status {status}".format(s=self, status=item.get('status')))
        maybe_remove(item, 'formats', 'requested_formats', 'tags')

        if self._url in self.state:
            state = self.state[self._url]
            if '_total_bytes_str' in state:
                maybe_remove(item, '_total_bytes_str')
            # seams like this dict proxi does not like a direct update
            state.update(item)
            self.state[self._url] = state
        else:
            self.state[self._url] = item

    def get_info(self, task):
        self._url = task.url
        self.inform({
            'status': 'analysing',
            'title': self._url,
            'thumbnail': '',
        })
        ydl_opts = {
            'skip_download': True,
            'dump_single_json': True,
            'call_home': False,
        }
        with YoutubeDL(ydl_opts) as ydl:
            r = ydl.download([task.url])

        self.inform({'status': 'done'})
        # we only gibe youtube-dl one url
        r = r[0]
        if 'entries' in r:
            r = r['entries']
        else:
            r = [r]
        return r


    def download(self, task):
        self._url = task.url
        ydl_opts = {
            'quiet': True,
            'progress_hooks': [self.inform],
            'dump_single_json': True,
            'call_home': False,
            'outtmpl': self.out_template,
            'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
            'writethumbnail': True,
            'cachedir': '/tmp',
            'merge_output_format': 'mp4',
            'download_archive': 'downloads/history.txt',
        }
        print("Starting download of " + self._url)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([self._url])


