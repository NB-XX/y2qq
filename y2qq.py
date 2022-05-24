import os
import PySimpleGUI as sg
import subprocess as sp
import youtube_dl
import yaml
import json
import requests
from bs4 import BeautifulSoup
import re
import time
import datetime

g_process = None


def set_proxy(in_port):
    port = in_port
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"

    ydl = youtube_dl.YoutubeDL()
    try:
        if ydl.urlopen("https://www.google.com").code == 200:
            sg.cprint('设置代理成功')
    except Exception as e:
        sg.cprint("请检测代理端口是否正确, 或对应代理软件是否已开放 http 代理")


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
            print(line)
    except Exception as e:
        import traceback
        err_str = traceback.format_exc()
        print(err_str)
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


def isLiveNow(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pattern = re.compile(r"var ytInitialPlayerResponse =(.*?);$",
                         re.MULTILINE | re.DOTALL)
    script = soup.find('script', text=pattern)
    data_str = pattern.search(script.text).group(1)
    data_json = json.loads(data_str, strict=False)
    # 获取设定开播时间 若已开播获取不到该部分
    try:
        isUpcoming = data_json["videoDetails"]["isUpcoming"]
        scheduledStartTime = data_json["playabilityStatus"]["liveStreamability"][
            "liveStreamabilityRenderer"]["offlineSlate"]["liveStreamOfflineSlateRenderer"]["scheduledStartTime"]
    except:
        isUpcoming = False
        scheduledStartTime = None
    isLiveNow = data_json["microformat"]["playerMicroformatRenderer"]["liveBroadcastDetails"]["isLiveNow"]
    check_result = [isUpcoming, isLiveNow, scheduledStartTime]
    print(check_result)
    return check_result


def check_live(url):
    check_result = isLiveNow(url)
    # 计算距离开播的秒数
    if check_result[0]:
        timediff = (int(check_result[2])-int(time.time()))
        sg.cprint(f'直播将于{timediff}s后开始')
        time.sleep(timediff-30)
    else:
        pass
        # 距直播还剩30s的时候开始反复检查是否开播
    while check_result[1] == False:
        now_time = datetime.datetime.now().strftime('%H:%M:%S')
        sg.cprint(f'{now_time} 还没有开播')
        time.sleep(15)
        check_result = isLiveNow(url)
    sg.cprint('直播开始了')
