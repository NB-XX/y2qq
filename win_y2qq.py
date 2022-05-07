import os

port = int(input('输入代理端口: '))
os.environ["http_proxy"] = f"http://127.0.0.1:{port}"
os.environ["https_proxy"] = f"http://127.0.0.1:{port}"
print('代理设置成功')
url = input('输入youtube直播链接: ')
get_url = os.popen(f'youtube-dl -g {url}')
print('别急 正在获取m3u8')
m3u8 = get_url.read()
print('m3u8获取成功')
get_url.close()
key = input('输入直播推流密钥: ')
os.system(
    f'ffmpeg -i {m3u8.strip()} -vcodec libx264 -acodec aac -f flv "rtmp://6721.livepush.myqcloud.com/live/{key}"')
