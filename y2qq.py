import os
import subprocess
import PySimpleGUI as sg

print = sg.Print


def resteam(in_youtube, in_ffmpeg, in_port, in_url, in_key):
    youtube_path = in_youtube
    ffmpeg_path = in_ffmpeg
    port = in_port
    url = in_url
    key = in_key
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"
    print('代理设置成功')
    get_url = os.popen(f'{youtube_path} -g {url}')
    print('别急 正在获取m3u8')
    m3u8 = get_url.read()
    print('m3u8获取成功')
    get_url.close()
    subprocess.Popen(
        f'{ffmpeg_path} -i {m3u8.strip()} -vcodec libx264 -acodec aac -f flv "rtmp://6721.livepush.myqcloud.com/live/{key}"')
