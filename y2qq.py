import os
import PySimpleGUI as sg
import subprocess as sp


def set_proxy(in_port):
    port = in_port
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"


def get_m3u8(in_youtube, in_url):
    youtube_path = in_youtube
    url = in_url
    m3u8 = os.popen(f'{youtube_path} -g {url}').read().strip()
    sg.cprint(f'获取m3u8成功')
    return m3u8

g_process = None
def restream(m3u8, in_ffmpeg, in_key):
    global g_process
    ffmpeg_path = in_ffmpeg
    key = in_key
    g_process = sp.Popen(
        [ffmpeg_path, '-i', m3u8, '-vcodec', 'libx264', '-acodec', 'aac', '-f', 'flv', f"rtmp://6721.livepush.myqcloud.com/live/{key}"], stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)
    for line in g_process.stdout:
        if 'speed' in line:
            sg.cprint(line.rstrip("\n"))

def stop_restream():    
    global g_process
    if g_process is not None:
        g_process.kill()