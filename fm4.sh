#!/bin/sh

PLS=http://mp3stream1.apasf.apa.at:8000/listen.pls
WMA=mms://apasf.apa.at/fm4_live_worldwide

FLINE=`wget -o - $PLS | grep File`
MP3="${FLINE##*=}"

URI=$MP3

echo $URI
gst-launch-0.10 playbin2 uri=$URI

