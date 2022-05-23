import os
import PySimpleGUI as sg
import subprocess as sp
import youtube_dl
import yaml


g_process = None


def set_proxy(in_port):
    port = in_port
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"
    sg.cprint('设置代理成功')


def get_format(in_url):
    url = in_url
    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
    try:
        with ydl:
            result = ydl.extract_info(f'{url}', download=False)
        if result['is_live']:
            sg.cprint('获取直播信息成功')
            return result['formats']
        else:
            sg.cprint('获取直播信息失败，直播可能已经停止')
    except:
        sg.cprint('检查直播链接输入是否正确')


def restream(m3u8, in_ffmpeg, in_key):
    global g_process
    ffmpeg_path = in_ffmpeg
    key = in_key
    try:
        g_process = sp.Popen(
            [ffmpeg_path, '-i', m3u8, '-vcodec', 'copy', '-acodec', 'aac', '-f', 'flv', f"rtmp://6721.livepush.myqcloud.com/live/{key}"], stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)
        for line in g_process.stdout:
            if 'speed' in line:
                sg.cprint(line.rstrip("\n"))
    except:
        sg.cprint('推流失败')


def stop_restream():
    global g_process
    if g_process is not None:
        g_process.kill()


def write_yaml(r):
    with open('config.yaml', "w", encoding="utf-8") as f:
        yaml.dump(r, f)


def read_yaml(file):
    try:
        with open(file, 'r') as f:
            yaml_dic = yaml.load(f, Loader=yaml.FullLoader)
        return yaml_dic
    except:
        sg.Popup('未发现保存的配置')
