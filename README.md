## 安装方法与依赖组件：

#### 安装方法：
windows端可直接运行编译好的y2qq.exe。  
其他平台下载本项目，用python运行y2qq_GUI.py即可。

#### 依赖：
## ffmpeg
https://ffmpeg.org/download.html  
## 依赖包
```
pip install -r .\requirements.txt
```

#### exe打包流程
   
1. 安装虚拟环境
```
pip install virtualenv
```

2. 创建虚拟环境
```
virtualenv win_pack
```

3. powershell运行权限设置 (如有)
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

4. 打开虚拟环境 (如使用IDE可直接选择环境)
```
./win_pack/Scripts/Activate.ps1
```

5. 运行打包
```
pip install -r .\requirements.txt
pyinstaller -wF --clean .\y2qq_GUI.py
```


 

## 快速上手：

1、了解你的代理工具所使用的端口  

在诸如clash、V2rayN、SSR之类的软件的设置界面中，都可以看到本地转发端口。  

一般默认端口设置如下：  
*clash for windows:**7890**  
ShadowsocksR:**1080**  
v2rayN:**10808***  

2、控件简介  

![控件简介](https://raw.githubusercontent.com/NB-XX/y2qq/main/res/example1.png)


左侧是输入区，右侧为通知/推流结果输出区。  
可以手动输入youtube-dl和ffmpeg所在路径，也可以通过选择文件按钮选择。  
*（tips：ffmpeg地址选择解压后bin文件夹下的ffmpeg.exe：  
当两个工具已经设置全局变量时，直接输入“youtube-d”l和“ffmpeg”即可）*  
点击保存配置可将三项固定设置写入当前文件夹下的config.yaml配置文件，多次保存会覆盖上一次的结果。  
直播密钥为在开播设置中获取的，以6721开头的一长串链接  




3、转播流程

![转播流程](https://raw.githubusercontent.com/NB-XX/y2qq/main/res/example2.gif)  
手动填好配置，或点击使用配置导入本地保存的配置后。再点击**设置代理**，设置成功后会在右侧输出框显示“设置代理成功”。  
输入直播链接，点击**获取m3u8**，成功后会在右侧输出框显示“获取m3u8成功”。  
输入直播密钥，点击**开始直播**，在输出栏有推流信息滚动即为推流成功。  
点击**停止直播**可以暂停直播，当没有重新获取m3u8的时候，点击**开始直播**可以继续上次直播。  

4、关于输出

frame：编码帧数量  
fps：每秒编码帧数  
q：质量因子  
speed：编码速度  

*（tips：直播推流只需关注speed即可，当speed小于1直播画面会有明显卡顿）*
### TODO LIST
- [X] 端口信息保存单独的配置文件
- [X] 可视化界面
- [X] 自动获取开播信息
