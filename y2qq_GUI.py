import os
import threading
from distutils.version import LooseVersion
import requests

import PySimpleGUI as sg

import y2qq
import updater
from m3u8_cache import m3u8_cache, server

EXE_VERSION = "2.2.0"

# start a local server
server.start_server()

format_dic = {
    "91": "144p",
    "92": "240p",
    "93": "360p",
    "94": "480p",
    "95": "720p",
    "96": "1080p",
    "300": "720p",
    "301": "1080p",
}
format_list = []
m3u8 = ""

sg.theme("DarkAmber")
# 设置控件属性
ff_text = sg.Text("设置ffmpeg路径")
ff_input = sg.Input("", key="ff", size=4)
port_text = sg.Text("输入代理端口")
port_input = sg.InputText(key="port", size=11)
port_button = sg.Button(
    "设置代理",
)
save_button = sg.Button("保存配置", key="save_yaml", size=14)
read_button = sg.Button("使用配置", key="read_yaml", size=14)
url_text = sg.Text("输入youtube链接")
url_input = sg.InputText(key="url", size=6)
m3u8_button = sg.Button("获取直播信息", size=9)
key_text = sg.Text("输入直播密钥")
key_input = sg.InputText(key="key", size=20)
output_Ml = sg.Multiline(
    key="Output", disabled=True, size=(50, 17), autoscroll=True, reroute_cprint=True
)
start_button = sg.Button("开始直播", size=14)
stop_button = sg.Button("停止推流", visible=False, size=14)
auto_live_check = sg.Button("挂机模式", key="-isLiveNow-")
format_list_text = sg.Text("选择分辨率")
format_list_selector = sg.Combo(
    format_list, key="-SELECTOR-", readonly=True, enable_events=True, size=20
)

# 左侧布局
left_col = [
    [sg.Button("更新版本", key="check_update", size=10)],
    [ff_text, ff_input, sg.FileBrowse("选择ffmpeg.exe")],
    [port_text, port_input, port_button],
    [save_button, read_button],
    [url_text, url_input, m3u8_button],
    [key_text, key_input],
    [format_list_text, format_list_selector],
    [start_button, stop_button],
]
layout = [[sg.Column(left_col), output_Ml]]


# ---temp function. Maybe move to outer file for better constuct
def btn_read_yaml_config(window):
    # 读取保存的配置并更新到控件
    try:
        dic = y2qq.read_yaml("config.yaml")
        tmp_ff_path = dic["ff"]
        if tmp_ff_path != "":
            window["ff"].update(tmp_ff_path)
        tmp_port = dic["port"]
        if tmp_port != "":
            window["port"].update(tmp_port)

        if dic.get("last_ytb_link"):
            window["url"].update(dic.get("last_ytb_link"))
        if dic.get("last_key"):
            window["key"].update(dic.get("last_key"))
        y2qq.set_proxy(dic["port"])
    except Exception as e:
        pass


def btn_save_config_yaml(values, should_pop_up=True):
    try:
        # 保存配置字典到当前文件夹
        dic = {
            "ff": values["ff"],
            "port": values["port"],
            "last_ytb_link": values["url"],
            "last_key": values["key"],
        }
        y2qq.write_yaml(dic)
        if should_pop_up:
            sg.Popup("保存配置成功")
    except:
        sg.Popup("写入配置失败")


def call_window_event_value_with_delay(
    window: sg.Window, key, value=None, delay: int = 0.1
):
    import time

    thread = threading.Thread(
        target=window.write_event_value, args=(key, value), daemon=True
    )
    time.sleep(delay)
    thread.start()


def check_update_info():
    response = requests.get("https://api.github.com/repos/NB-XX/y2qq/releases/latest")
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
        if tmp_version > LooseVersion(EXE_VERSION):
            assets = info_dict["assets"]
            sg.cprint("正在更新中。。。请稍等\n更新期间请勿操作\n如长时间没反应,请检测网络和代理设置.\n然后关闭应用重新再打开")
            update_exe(assets, window)
        else:
            sg.popup(f"当前版本:{EXE_VERSION}; 最新版本: {tmp_version}, 暂不需要更新")
    except Exception as e:
        sg.popup("更新失败, 请检测网络或设置代理后重试")


def update_exe(assets, window: sg.Window):
    thread = threading.Thread(target=__update_exe, args=(assets, window), daemon=True)
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


def windows_init(window: sg.Window):
    btn_read_yaml_config(window)
    call_window_event_value_with_delay(window, "获取直播信息")


# ---windows init and event loop
try:
    window = sg.Window("QQ频道转播", layout, finalize=True)

    windows_init(window)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == "设置代理":
            try:
                tmp_port = int(values["port"])
                y2qq.set_proxy(values["port"])
            except:
                sg.Popup("请输入端口数字")
        elif event == "获取直播信息":
            # 开启新进程获取直播信息
            window.perform_long_operation(
                lambda: y2qq.get_format(values["url"]), "-format-"
            )
        elif event == "-format-":
            # 获取清晰度参数format
            try:
                # 每次更新时需要先清空,否则按多次时无限添加
                format_list = []
                formats = values[event]
                for i in formats:
                    format_list.append(format_dic[i["format_id"]])
                # 调用字典转化为分辨率并更新到选择列表
                window["-SELECTOR-"].update(values=format_list)
            except:
                pass
        elif event == "-SELECTOR-":
            # 通过列表选择器的输入提取对应的m3u8链接
            index = format_list.index(values["-SELECTOR-"])
            m3u8 = formats[index]["url"]
            sg.cprint(f"当前选择:{m3u8}")
        elif event == "开始直播":
            try:
                # 取代远端 m3u8, 本地读取 m3u8 合并多个Seq
                video_id = values["url"].split("v=")[1].strip()
                local_m3u8_url = m3u8_cache.server_produce_m3u8(video_id, m3u8)
                sg.cprint(f"本地 m3u8 url:\n{local_m3u8_url}")

                # 开启新进程 用于持续打印推流情况
                window.perform_long_operation(
                    lambda: y2qq.restream(local_m3u8_url, values["ff"], values["key"]),
                    "-restream-",
                )
                window["停止推流"].update(visible=True)
                btn_save_config_yaml(values, should_pop_up=False)
            except Exception as e:
                sg.Popup("推流失败,检查密钥和ffmpeg是否配置正确")
        elif event == "-restream-":
            pass
        elif event == "-isLiveNow-":
            window.perform_long_operation(
                lambda: y2qq.check_live(values["url"]), "-check-"
            )
        elif event == "-check-":
            pass
        elif event == "停止推流":
            y2qq.stop_restream()
            m3u8_cache.stop_server_produce_m3u8()
            sg.cprint("推流已经停止")
        elif event == "save_yaml":
            btn_save_config_yaml(values)
        elif event == "read_yaml":
            btn_read_yaml_config(window)
        elif event == "check_update":
            check_update(window)
        elif event == "-Missing_Updater-":
            sg.popup("找不到updater.exe")
        else:
            sg.Popup(f"未处理未知事件:【{event}】")
except Exception as e:
    import traceback

    err_str = traceback.format_exc()
    sg.Popup(f"未处理异常:【{err_str}】")
finally:
    server.shutdown_server()
    window.close()
