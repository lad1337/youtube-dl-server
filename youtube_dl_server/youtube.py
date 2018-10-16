from datetime import datetime
import os
import re

import youtube_dl as ydl
from youtube_dl.utils import UnavailableVideoError
from youtube_dl import YoutubeDL as YoutubeDL_

from multiprocessing import Process

#DEFAULT_TEMPLATE = "%(title)s.%(ext)s"
#DEFAULT_TEMPLATE = "%(uploader)s [%(channel_id)s]/%(playlist)s [%(playlist_id)s]/%(title)s [%(id)s].%(ext)s"
# https://forums.plex.tv/t/rel-youtube-metadata-agent/44574/133
"""
- Playlist [PLxxxxxxx]/file [xxxxxxx].ext
- Uploader (also called channel) [UCxxxxxxx]/Folder x/file [xxxxxxx].ext
- Uploader (also called channel) [UCxxxxxxx]|Subject/Playlist [PLxxxxxxx]/file [xxxxxxx].ext
- eg: /Cody’s Lab [UCu6mSoMNzHQiBIOCkHUa2Aw]/24K Pure Gold Foil Ball [bt2BDCwu18U].mp4
The uploader/Channel will become a collection, The playlist a series, The files episodes.
"""
DEFAULT_TEMPLATE = "%(playlist)s [%(playlist_id)s]/%(title)s [%(id)s].%(ext)s"


class YoutubeDL(YoutubeDL_):
    def download(self, url_list, extra=None):
        """Download a given list of URLs."""
        extra = extra or {}
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
                    url,
                    force_generic_extractor=self.params.get('force_generic_extractor', False),
                    extra_info=extra,
                )
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
            try:
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
            finally:
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
        #print("Inform {s._url} status {status}".format(s=self, status=item.get('status')))
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
        self.inform({'status': 'analysing', 'title': self._url, 'thumbnail': ''})
        # [download] Downloading video 4 of 16
        pattern = re.compile("video (?P<index>\d+) of (?P<total>\d+)")


        def debug(message):
            match = pattern.search(message)
            if match is not None:
                percent = 100 / (float(match.group('total')) / float(match.group('index')))
                self.inform({
                    '_percent_str': f"{percent}%",
                })
        fake_logger = type('f', tuple(), {'debug': debug})

        ydl_opts = {
            'logger': fake_logger,
            'quiet': True,
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
            'skip_download': os.environ.get('YTDL_SKIPDL', False),
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
            ydl.download([self._url], self.state[self._url])
        self.inform({'status': 'done'})


