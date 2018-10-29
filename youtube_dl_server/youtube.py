from datetime import datetime
from multiprocessing import Process
import os
import re

import youtube_dl as ydl
from youtube_dl.utils import UnavailableVideoError
from youtube_dl import YoutubeDL as YoutubeDL_

from youtube_dl_server.utils import attribute
from youtube_dl_server.utils import maybe_remove

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
                raise
            except ydl.MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloaded files reached.')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    out.append(res)

        return out


class Task:
    def __init__(self, url, info=None, title_filter=None, index_filter=None):
        self.url = url
        self.info = info or {}
        self.title_filter = title_filter
        self.index_filter = index_filter
        if index_filter is not None:
            filter_ = set()
            for i in index_filter.split(','):
                if '-' in i:
                    begin, _, end = i.partition('-')
                    filter_.update(range(int(begin), int(end) + 1))
                else:
                    filter_.add(int(i))

            self.index_filter = filter_

    @property
    def is_playlist(self):
        return 'playlist' in self.url

    @property
    def investigate(self):
        return not self.info

    @classmethod
    def from_info(cls, info):
        return cls(info['webpage_url'], info=info)

    def new_for(self, info):
        if self.title_filter is not None and self.title_filter not in info['title']:
            return
        if self.index_filter is not None and info['playlist_index'] not in self.index_filter:
            return
        return Task.from_info(info)


class YTWorker(Process):

    def __init__(self, queue, state, template=DEFAULT_TEMPLATE ,download=True, proxy=None, *args, **kwargs):
        super(YTWorker, self).__init__(*args, **kwargs)
        self.queue = queue
        self.state = state
        self.should_download = download
        self.out_template = template
        self.task = None
        self.proxy = proxy
        self.proxy.busy = False

    @property
    def url(self):
        return self.task.url

    def __str__(self):
        s = super(YTWorker, self).__str__()
        type_ = "downloader" if self.should_download else "info getter"
        return "{} {}".format(s, type_)

    def run(self):
        print("Started {}".format(self))
        while True:
            self.task = self.queue.get()
            self.proxy.busy = True
            try:
                if self.task.investigate:
                    self.investigate(self.task)
                elif self.should_download:
                    self.download(self.task)
                else:
                    print(f"re queueing ... but why? {self.task}")
                    self.queue.put(self.task)
            except:
                self.inform({'status': 'error'})
                raise
            else:
                self.proxy.busy = False
            finally:
                self.queue.task_done()

    def investigate(self, task):
        entries = self.get_info(task)
        for info in entries:
            t = task.new_for(info)
            if t is None:
                continue
            with attribute(self, 'task', t):
                self.inform(t.info)
            self.queue.put(t)

    def inform(self, item=None):
        item['updated_at'] = datetime.now().timestamp()
        #print("Inform {s._url} status {status}".format(s=self, status=item.get('status')))
        maybe_remove(item, 'formats', 'requested_formats', 'tags')

        if self.url in self.state:
            state = self.state[self.url]
            if '_total_bytes_str' in state:
                maybe_remove(item, '_total_bytes_str')
            # seams like this dict proxi does not like a direct update
            state.update(item)
            self.state[self.url] = state
        else:
            self.state[self.url] = item

    def get_info(self, task):
        self.inform({'status': 'analysing', 'title': self.url, 'thumbnail': ''})
        # [download] Downloading video 4 of 16
        pattern = re.compile("video (?P<index>\d+) of (?P<total>\d+)")

        def parser(message):
            match = pattern.search(message)
            if match is not None:
                percent = 100 / (float(match.group('total')) / float(match.group('index')))
                self.inform({
                    '_percent_str': f"{percent}%",
                })
        fake_logger = type('f', tuple(), {'debug': parser, 'warning': parser})

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
        print("Starting download of " + self.url)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([task.url], extra=task.info)
        self.inform({'status': 'done'})


