import PySimpleGUI as sg
import y2qq

format_dic = {
    '91 - 256x144': '144p', '92 - 426x240': '240p', '93 - 640x360': '360p', '94 - 854x480': '480p', '300 - 1280x720': '720p', '301 - 1920x1080': '1080p'
}
format_list = []
m3u8 = ''
sg.theme('DarkAmber')
# 设置控件属性
ff_text = sg.Text('设置ffmpeg路径')
ff_input = sg.Input('', key='ff', size=4)
port_text = sg.Text('输入代理端口')
port_input = sg.InputText(key='port', size=11)
port_button = sg.Button('设置代理',)
save_button = sg.Button('保存配置', key='save_yaml', size=14)
read_button = sg.Button('使用配置', key='read_yaml', size=14)
url_text = sg.Text('输入youtube链接')
url_input = sg.InputText(key='url', size=6)
m3u8_button = sg.Button('获取直播信息', size=9)
key_text = sg.Text('输入直播密钥')
key_input = sg.InputText(key='key', size=20)
output_Ml = sg.Multiline(key='Output', disabled=True,
                         size=(50, 17), autoscroll=True, reroute_cprint=True)
start_button = sg.Button('开始直播', size=14)
stop_button = sg.Button('停止推流', visible=False, size=14)
format_list_text = sg.Text('选择分辨率')
format_list_selector = sg.Combo(
    format_list, key='-SELECTOR-', readonly=True, enable_events=True, size=20)

# 左侧布局
left_col = [
    [ff_text, ff_input, sg.FileBrowse('选择ffmpeg.exe')],
    [port_text, port_input, port_button],
    [save_button, read_button],
    [url_text, url_input, m3u8_button],
    [key_text, key_input],
    [format_list_text, format_list_selector],
    [start_button, stop_button]]
layout = [
    [sg.Column(left_col), output_Ml]
]


try:
    window = sg.Window('QQ频道转播', layout)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == '设置代理':
            if values['port'] == None:
                sg.Popup('请输入端口数字')
            else:
                y2qq.set_proxy(values['port'])
        elif event == '获取直播信息':
            # 开启新进程获取直播信息
            window.perform_long_operation(
                lambda: y2qq.get_format(values['url']), '-format-')
        elif event == '-format-':
            # 获取清晰度参数format
            try:
                formats = values[event]
                for i in formats:
                    format_list.append(format_dic[i['format']])
                # 调用字典转化为分辨率并更新到选择列表
                window['-SELECTOR-'].update(values=format_list)
            except:
                pass
        elif event == '-SELECTOR-':
            # 通过列表选择器的输入提取对应的m3u8链接
            index = format_list.index(values['-SELECTOR-'])
            m3u8 = formats[index]["url"]
            print(m3u8)
        elif event == '开始直播':
            try:
                # 开启新进程 用于持续打印推流情况
                window.perform_long_operation(
                    lambda: y2qq.restream(m3u8, values['ff'], values['key']), '-restream-')
                window['停止推流'].update(visible=True)
            except:
                sg.Popup('推流失败,检查密钥和ffmpeg是否配置正确')
        elif event == '-restream-':
            pass
        elif event == '停止推流':
            y2qq.stop_restream()
            sg.cprint('推流已经停止')
        elif event == 'save_yaml':
            try:
                # 保存配置字典到当前文件夹
                dic = {'ff': values['ff'],
                       'port': values['port']}
                y2qq.write_yaml(dic)
                sg.Popup('保存配置成功')
            except:
                sg.Popup('写入配置失败')
        elif event == 'read_yaml':
            # 读取保存的配置并更新到控件
            try:
                dic = y2qq.read_yaml('config.yaml')
                window['ff'].update(dic['ff'])
                window['port'].update(dic['port'])
                y2qq.set_proxy(dic['port'])
            except:
                pass
        else:
            sg.Popup(f"未处理未知事件:【{event}】")
except Exception as e:
    import traceback
    err_str = traceback.format_exc()
    sg.Popup(f"未处理异常:【{err_str}】")
finally:
    window.close()
