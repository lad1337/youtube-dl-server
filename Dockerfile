FROM python:alpine as builder

RUN apk --update add --no-cache git

ARG whl=/tmp/wheelhouse
WORKDIR /tmp
COPY . .
RUN pip wheel --wheel-dir=${whl} .

FROM python:alpine
RUN apk --update add ffmpeg

# write your package name here with _
ARG PACKAGENAME=youtube_dl_server
ARG whl=/tmp/wheelhouse
COPY --from=builder ${whl} ${whl}
RUN pip install --find-links ${whl} ${whl}/${PACKAGENAME}-*.whl
RUN rm -r ${whl}

EXPOSE 8080

ENV YTDL_ROOT="/downloads"
VOLUME ["/youtube-dl"]

CMD ["youtube-dl-server"]
