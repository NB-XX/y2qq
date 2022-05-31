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

import threading
from distutils.version import LooseVersion

import updater
from m3u8_cache import m3u8_cache
from VERSION import EXE_VERSION

g_process = None


def set_proxy(in_port):
    port = in_port
    os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
    os.environ["https_proxy"] = f"http://127.0.0.1:{port}"

    ydl = youtube_dl.YoutubeDL()
    try:
        if ydl.urlopen("https://www.google.com").code == 200:
            sg.cprint("设置代理成功")
    except Exception as e:
        sg.cprint("请检测代理端口是否正确, 或对应代理软件是否已开放 http 代理")


def get_format(in_url):
    url = in_url
    ydl = youtube_dl.YoutubeDL({"outtmpl": "%(id)s.%(ext)s"})
    try:
        with ydl:
            result = ydl.extract_info(f"{url}", download=False)
        if result["is_live"]:
            sg.cprint("获取直播信息成功")
            return result
        else:
            sg.cprint("获取直播信息失败，直播可能已经停止")
    except:
        sg.cprint("检查直播链接输入是否正确")


def __refresh_remote_m3u8(video_id, video_url, select_format="480p"):
    format_list = get_format(video_url)
    select_format = select_format.strip("p")

    result_url = None
    for f in format_list:
        height = f["height"]
        if str(height) == select_format:
            result_url = f["url"]

    if result_url == None:
        result_url = format_list[0]["url"]

    m3u8_cache.setup_m3u8_src(video_id, result_url)


def restream(m3u8, video_id, selected_format, in_ffmpeg, in_server_url, in_key):
    global g_process
    stop_restream()

    # 取代远端 m3u8, 本地读取 m3u8 合并多个Seq
    video_id = video_id
    m3u8_cache.setup_m3u8_src(video_id, m3u8)
    local_m3u8_url = m3u8_cache.server_produce_m3u8(video_id, m3u8)
    sg.cprint(f"本地 m3u8 url:\n{local_m3u8_url}")

    using_m3u8 = local_m3u8_url

    ffmpeg_path = in_ffmpeg
    server_url = in_server_url if in_server_url.endswith(
        "/") else in_server_url + "/"
    key = in_key

    # FFMPEG 命令
    # --------------------
    run_args = []
    run_args += [ffmpeg_path]

    # run_args += ["-thread_queue_size", "4"]

    run_args += ["-re"]
    run_args += ["-i", using_m3u8]
    run_args += ["-vcodec", "copy", "-acodec", "aac"]

    run_args += ["-f", "flv"]
    run_args += [f"{server_url}{key}"]
    # --------------------

    try:
        g_process = sp.Popen(
            run_args,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            universal_newlines=True,
            creationflags=sp.CREATE_NO_WINDOW,
        )
        trigger_time = 0
        for line in g_process.stdout:
            if "speed" in line:
                sg.cprint(line.rstrip("\n"))

                # 三次推送速度过慢时, 尝试重新获取远端m3u8
                try:
                    speed = line.split("speed=")[-1].split("x")[0].strip()
                    if float(speed) < 0.8:
                        trigger_time += 1
                        if trigger_time > 3:
                            __refresh_remote_m3u8(
                                video_id, video_url, selected_format)
                            trigger_time = 0
                except Exception as e:
                    pass
            elif "Error " in line:
                sg.cprint(line.rstrip("\n"))
                print(line)

        # for out putting the end of process
        stop_restream()
    except Exception as e:
        import traceback

        err_str = traceback.format_exc()
        sg.cprint(err_str)
        sg.cprint("推流失败")
        stop_restream()


def stop_restream():
    global g_process
    if g_process is not None:
        g_process.kill()
    m3u8_cache.stop_server_produce_m3u8()


def write_yaml(r):
    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(r, f)


def read_yaml(file):
    try:
        with open(file, "r") as f:
            yaml_dic = yaml.load(f, Loader=yaml.FullLoader)
        return yaml_dic
    except:
        sg.Popup("未发现保存的配置")


def isLiveNow(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pattern = re.compile(
        r"var ytInitialPlayerResponse =(.*?);$", re.MULTILINE | re.DOTALL
    )
    script = soup.find("script", text=pattern)
    data_str = pattern.search(script.text).group(1)
    data_json = json.loads(data_str, strict=False)
    # 获取设定开播时间 若已开播获取不到该部分
    try:
        isUpcoming = data_json["videoDetails"]["isUpcoming"]
        scheduledStartTime = data_json["playabilityStatus"]["liveStreamability"][
            "liveStreamabilityRenderer"
        ]["offlineSlate"]["liveStreamOfflineSlateRenderer"]["scheduledStartTime"]
    except:
        isUpcoming = False
        scheduledStartTime = None
    isLiveNow = data_json["microformat"]["playerMicroformatRenderer"][
        "liveBroadcastDetails"
    ]["isLiveNow"]
    check_result = [isUpcoming, isLiveNow, scheduledStartTime]
    print(check_result)
    return check_result


def check_live(url):
    check_result = isLiveNow(url)
    # 计算距离开播的秒数
    if check_result[0]:
        timediff = int(check_result[2]) - int(time.time())
        sg.cprint(f"直播将于{timediff}s后开始")
        time.sleep(timediff - 30)
    else:
        pass
        # 距直播还剩30s的时候开始反复检查是否开播
    while check_result[1] == False:
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        sg.cprint(f"{now_time} 还没有开播")
        time.sleep(15)
        check_result = isLiveNow(url)
    sg.cprint("直播开始了，开始自动推流最高画质")


def check_update_info():
    response = requests.get(
        "https://api.github.com/repos/NB-XX/y2qq/releases/latest")
    info_dict = response.json()
    return info_dict


def download_file(url, parent_path=updater.g_update_path):
    local_filename = url.split("/")[-1]
    os.makedirs(parent_path, exist_ok=True)
    fp = os.path.join(parent_path, local_filename)
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(fp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return fp


def check_update(window: sg.Window):
    try:
        info_dict = check_update_info()
        tag_name = info_dict["tag_name"]
        tmp_version = tag_name.strip("v")
        if LooseVersion(tmp_version) > LooseVersion(EXE_VERSION):
            assets = info_dict["assets"]
            sg.cprint("正在更新中。。。请稍等\n更新期间请勿操作\n如长时间没反应,请检测网络和代理设置.\n然后关闭应用重新再打开")
            update_exe(assets, window)
        else:
            sg.popup(f"当前版本:{EXE_VERSION}; 最新版本: {tmp_version}, 暂不需要更新")
    except Exception as e:
        sg.popup("更新失败, 请检测网络或设置代理后重试")


def update_exe(assets, window: sg.Window):
    thread = threading.Thread(
        target=__update_exe, args=(assets, window), daemon=True)
    thread.start()


def __update_exe(assets, window: sg.Window):
    import os
    from subprocess import Popen

    for file in assets:
        if file["name"].endswith(".exe"):
            download_url = file["browser_download_url"]
            download_file(download_url)
    try:
        Popen(os.path.join(os.getcwd(), "updater.exe"))
        window.write_event_value(sg.WIN_CLOSED, None)
    except FileNotFoundError as e:
        window.write_event_value("-Missing_Updater-", None)
