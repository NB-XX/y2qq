import os
import PySimpleGUI as sg
import subprocess as sp

print = sg.Print


def set_proxy(in_port):
    port = in_port
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"


def get_m3u8(in_youtube, in_url):
    youtube_path = in_youtube
    url = in_url
    m3u8 = os.popen(f'{youtube_path} -g {url}').read().strip()
    return m3u8


def resteam(m3u8, in_ffmpeg, in_key):
    ffmpeg_path = in_ffmpeg
    key = in_key
    process = sp.Popen(
        f'{ffmpeg_path} -i {m3u8} -vcodec libx264 -acodec aac -f flv "rtmp://6721.livepush.myqcloud.com/live/{key}"', stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)
    for line in process.stdout:
        print(line)
