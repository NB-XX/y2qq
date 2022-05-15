import PySimpleGUI as sg
import y2qq


sg.theme('DarkAmber')
layout = [[sg.Text('设置youtube-dl地址'), sg.Input(), sg.FileBrowse(), sg.Text('设置ffmpeg地址'), sg.Input(), sg.FileBrowse()],
          [sg.Text('输入代理端口'), sg.InputText()],
          [sg.Text('输入youtube链接'), sg.InputText()],
          [sg.Text('输入直播密钥'), sg.InputText()],
          [sg.Button('确认'), sg.Button('关闭')]]


window = sg.Window('QQ频道转播', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == '关闭':  # if user closes window or clicks cancel
        break
    y2qq.resteam(values[0], values[1], values[2], values[3], values[4])

window.close()
