import PySimpleGUI as sg
import y2qq


sg.theme('DarkAmber')
layout = [[sg.Text('设置youtube-dl地址'), sg.Input('youtube-dl', key='yt'), sg.FileBrowse(), sg.Text('设置ffmpeg地址'), sg.Input('ffmpeg', key='ff'), sg.FileBrowse()],
          [sg.Text('输入代理端口'), sg.InputText(key='port'),
           sg.Button('设置代理')],
          [sg.Button('保存配置', key='save_yaml'),
           sg.Button('使用配置', key='read_yaml')],
          [sg.Text('输入youtube链接'),
           sg.InputText(key='url'), sg.Button('获取m3u8')],
          [sg.Text('输入直播密钥'), sg.InputText(key='key')],
          [sg.Multiline(key='Output', disabled=True,
                        size=(80, 6), autoscroll=True, reroute_cprint=True)],
          [sg.Button('开始直播'), sg.Button('停止推流')]]

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
        window.perform_long_operation(
            lambda: y2qq.get_m3u8(values['yt'], values['url']), '-m3u8-')
    if event == '-m3u8-':
        m3u8 = values[event]
    if event == '开始直播':
        try:
            window.perform_long_operation(
                lambda: y2qq.restream(m3u8, values['ff'], values['key']), '-restream')
        except:
            sg.Popup('推流失败，检查m3u8、密钥和ffmpeg是否配置正确')
    if event == 'save_yaml':
        try:
            dic = {'yt': values['yt'], 'ff': values['ff'],
                   'port': values['port']}
            with open('config.yaml', 'w') as f:
                f.write(str(dic))
            sg.Popup('保存配置成功')
        except:
            sg.Popup('写入配置失败')
    if event == 'read_yaml':
        try:
            with open('config.yaml', 'r') as f:
                dic = eval(f.read())
                window['yt'].update(dic['yt'])
                window['ff'].update(dic['ff'])
                window['port'].update(dic['port'])
            y2qq.set_proxy(values['port'])
        except:
            sg.Popup('配置导入失败，检查配置文件是否存在')
window.close()
