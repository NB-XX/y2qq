import PySimpleGUI as sg
import y2qq


sg.theme('DarkAmber')
layout = [[sg.Text('设置youtube-dl地址'), sg.Input(), sg.FileBrowse(), sg.Text('设置ffmpeg地址'), sg.Input(), sg.FileBrowse()],
          [sg.Text('输入代理端口'), sg.InputText(), sg.Button('设置代理')],
          [sg.Text('输入youtube链接'), sg.InputText(), sg.Button('获取m3u8')],
          [sg.Text('输入直播密钥'), sg.InputText()],
          [sg.Button('开始直播'), sg.Button('停止')]]

window = sg.Window('QQ频道转播', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == '停止':  # if user closes window or clicks cancel
        break
    if event == '设置代理':
        y2qq.set_proxy(values[2])
        sg.Popup('设置代理成功')
    if event == '获取m3u8':
        m3u8 = y2qq.get_m3u8(values[0], values[3])
        sg.Popup('获取m3u8成功')
    if event == '开始直播':
        try:
            y2qq.resteam(m3u8, values[1], values[4])
        except:
            sg.Popup('检查m3u8是否获取成功')
window.close()
