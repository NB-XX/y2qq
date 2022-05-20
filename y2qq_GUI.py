import PySimpleGUI as sg
import y2qq

sg.theme('DarkAmber')
# 设置控件属性
yt_text = sg.Text('设置youtube-dl路径')
yt_input = sg.Input('', key='yt', size=6)
ff_text = sg.Text('设置ffmpeg路径')
ff_input = sg.Input('', key='ff', size=9)
port_text = sg.Text('输入代理端口')
port_input = sg.InputText(key='port', size=11)
port_button = sg.Button('设置代理',)
save_button = sg.Button('保存配置', key='save_yaml', size=14)
read_button = sg.Button('使用配置', key='read_yaml', size=14)
url_text = sg.Text('输入youtube链接')
url_input = sg.InputText(key='url', size=6)
m3u8_button = sg.Button('获取m3u8', size=9)
key_text = sg.Text('输入直播密钥')
key_input = sg.InputText(key='key', size=20)
output_Ml = sg.Multiline(key='Output', disabled=True,
                         size=(50, 17), autoscroll=True, reroute_cprint=True)
start_button = sg.Button('开始直播', size=14)
stop_button = sg.Button('停止推流', size=14)

# 左侧布局
left_col = [[yt_text, yt_input, sg.FileBrowse('选择文件')],
            [ff_text, ff_input, sg.FileBrowse('选择文件')],
            [port_text, port_input, port_button],
            [save_button, read_button],
            [url_text, url_input, m3u8_button],
            [key_text, key_input],
            [start_button, stop_button]]
layout = [
    [sg.Column(left_col), output_Ml]
]

window = sg.Window('QQ频道转播', layout)
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == '停止推流':
        y2qq.process.kill()
        sg.cprint('推流已经停止')
    if event == '设置代理':
        if values['port'] == None:
            sg.Popup('请输入端口数字')
        else:
            y2qq.set_proxy(values['port'])
            sg.cprint('设置代理成功')
    if event == '获取m3u8':
        # 开启新进程获取m3u8
        window.perform_long_operation(
            lambda: y2qq.get_m3u8(values['yt'], values['url']), '-m3u8-')
    if event == '-m3u8-':
        m3u8 = values[event]
    if event == '开始直播':
        try:
            # 开启新进程 用于持续打印推流情况
            window.perform_long_operation(
                lambda: y2qq.restream(m3u8, values['ff'], values['key']), '-restream')
        except:
            sg.Popup('推流失败，检查m3u8、密钥和ffmpeg是否配置正确')
    if event == 'save_yaml':
        try:
            # 保存配置字典到当前文件夹
            dic = {'yt': values['yt'], 'ff': values['ff'],
                   'port': values['port']}
            with open('config.yaml', 'w') as f:
                f.write(str(dic))
            sg.Popup('保存配置成功')
        except:
            sg.Popup('写入配置失败')
    if event == 'read_yaml':
        try:
            # 读取保存的配置并更新到控件
            with open('config.yaml', 'r') as f:
                dic = eval(f.read())
                window['yt'].update(dic['yt'])
                window['ff'].update(dic['ff'])
                window['port'].update(dic['port'])
            y2qq.set_proxy(values['port'])
        except:
            sg.Popup('配置导入失败，检查配置文件是否存在')
window.close()
