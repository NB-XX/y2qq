import threading
import time
import PySimpleGUI as sg

import y2qq
from m3u8_cache import server


# start a local server
server.start_server()

format_list = []
g_current_selected_format = 0
g_current_m3u8_url = ""

sg.theme("DarkAmber")
# 设置控件属性
update_button = sg.Button("更新版本", key="check_update", size=10)
auto_live_check = sg.Button("挂机模式", key="-isLiveNow-")
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
live_server_text = sg.Text("输入直播服务器")
live_server_input = sg.Input(
    key="live_server", size=20, default_text="rtmp://6721.livepush.myqcloud.com/live/"
)
output_Ml = sg.Multiline(
    key="Output", disabled=True, size=(50, 17), autoscroll=True, reroute_cprint=True
)
start_button = sg.Button("开始直播", size=14)
stop_button = sg.Button("停止推流", visible=False, size=14)
format_list_text = sg.Text("选择分辨率")
format_list_selector = sg.Combo(
    format_list, key="-SELECTOR-", readonly=True, enable_events=True, size=20
)
tilte_text = sg.Text("", key="-title-")
main_tab = [
    [url_text, url_input, m3u8_button],
    [format_list_text, format_list_selector],
    [start_button, stop_button],
    [auto_live_check],
    [tilte_text],
]
setting_tab = [
    [update_button],
    [ff_text, ff_input, sg.FileBrowse("选择ffmpeg.exe")],
    [port_text, port_input, port_button],
    [live_server_text, live_server_input],
    [key_text, key_input],
    [save_button, read_button],
]
# 左侧布局

layout = [
    [
        sg.TabGroup(
            [[sg.Tab("主页", main_tab), sg.Tab("设置", setting_tab)]],
            key="-group1-",
            tab_location="right",
        )
    ],
    [output_Ml],
]


# ---temp function. Maybe move to outer file for better constuct
def btn_read_yaml_config(window: sg.Window):
    # 读取保存的配置并更新到控件
    try:
        dic = y2qq.read_yaml("config.yaml")
        tmp_ff_path = dic.get("ff", "")
        if tmp_ff_path != "":
            window["ff"].update(tmp_ff_path)
        tmp_port = dic.get("port", "")
        if tmp_port != "":
            window["port"].update(tmp_port)

        tmp_live_server = dic.get("live_server", "")
        if tmp_live_server != "":
            window["live_server"].update(tmp_live_server)

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
            "live_server": values["live_server"],
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
                formats_raw = values[event]
                formats = formats_raw["formats"]
                format_list = [f"{f['height']}p" for f in formats]
                window["-SELECTOR-"].update(values=format_list)

                call_window_event_value_with_delay(
                    window, "-SELECTOR-", format_list[-1]
                )
                window["-title-"].update(formats_raw["title"][:-17])
            except:
                pass
        elif event == "-SELECTOR-":
            # 通过列表选择器的输入提取对应的m3u8链接
            g_current_selected_format = values["-SELECTOR-"]
            index = format_list.index(values["-SELECTOR-"])

            # 选择对应Index，用于自动触发时
            window["-SELECTOR-"].update(set_to_index=[index])

            g_current_m3u8_url = formats[index]["url"]
            sg.cprint(f"当前选择:{g_current_selected_format}")
        elif event == "开始直播":
            try:
                btn_save_config_yaml(values, should_pop_up=False)

                # 开启新进程 用于持续打印推流情况
                window.perform_long_operation(
                    lambda: y2qq.restream(
                        g_current_m3u8_url,
                        formats_raw["id"],
                        g_current_selected_format,
                        values["ff"],
                        values["live_server"],
                        values["key"],
                    ),
                    "-restream-",
                )
                window["停止推流"].update(visible=True)
            except Exception as e:
                sg.Popup("推流失败,检查密钥和ffmpeg是否配置正确")
        elif event == "-restream-":
            pass
        elif event == "-isLiveNow-":
            window.perform_long_operation(
                lambda: y2qq.check_live(values["url"]), "-check-"
            )
        elif event == "-check-":
            window.write_event_value("获取直播信息", "** DONE **")

            is_auto_live_OK = False
            tmp_retry_times = 0
            while True:
                if g_current_m3u8_url:
                    window.write_event_value("获取直播信息", "** DONE **")
                    call_window_event_value_with_delay(
                        window, "开始直播", g_current_m3u8_url, delay=1
                    )
                    is_auto_live_OK = True
                    break
                else:
                    if tmp_retry_times > 10:
                        is_auto_live_OK = False
                        break
                    tmp_retry_times += 1
                    time.sleep(1)
            if is_auto_live_OK == False:
                sg.popup("自动开播失败, 请检测网络")
        elif event == "停止推流":
            y2qq.stop_restream()
            sg.cprint("推流已经停止")
        elif event == "save_yaml":
            btn_save_config_yaml(values)
        elif event == "read_yaml":
            btn_read_yaml_config(window)
        elif event == "check_update":
            y2qq.check_update(window)
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
