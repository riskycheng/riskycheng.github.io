---
layout: wiki
title: FFMPEG 在Windows上推拉流
cate1: Utils
cate2:
description: ffmpeg
keywords: ffmpeg
---

## 概述
[FFMPEG](https://ffmpeg.org/download.html)可以用于RTSP的推流测试，用于本地测试RTSP的模拟运行环境，可以使用VLC等多媒体播放器进行拉流。

## 下载安装FFMPEG
[FFmpeg官网](https://ffmpeg.org/download.html) 下载 Windows 版本的 FFmpeg，并把 FFmpeg 的 bin 目录加入到环境变量中。


## 下载安装 EasyDarwin
[EasyDarwin 下载地址](https://github.com/EasyDarwin/EasyDarwin/releases)
下载解压到本地后运行 EasyDarwin.exe 程序。点击运行后会弹出一个 cmd 命令框，在浏览器中输入 http://127.0.0.1:10008 查看是否有显示有个 web 页面，如果显示则证明打开成功。注：不要关闭弹出的命令框：
![](https://note.youdao.com/yws/api/personal/file/WEBd16abdad7fbce45117d439256327c050?method=download&shareKey=9fa7b06a77a9d8f4969b016b4beb1423)


![](https://note.youdao.com/yws/api/personal/file/WEB228bd316ad9582a241b23748775da0b3?method=download&shareKey=6e2d0e40fb85587db425f6dfb20196a7)



## 使用 FFmpeg 获取 DirectShow 设备
```
ffmpeg -list_devices true -f dshow -i dummy
```
![](https://note.youdao.com/yws/api/personal/file/WEBe76912d8e60f6c783468f1e48bdc1c62?method=download&shareKey=2598daa8c8a2d8c108834e5893d676ed)
## 推送摄像头到 rtsp 服务器
```
ffmpeg -f dshow -i video="Logitech Webcam C930e" -vcodec libx264 -preset:v ultrafast -tune:v zerolatency -rtsp_transport tcp -f rtsp rtsp://127.0.0.1/test
```
运行后可以在上方打开的 EasyDarwin 的 web 页面中的推流列表中查看是否有 rtsp 流的地址。

## 推送视频到 rtsp 服务器
```
ffmpeg -re -stream_loop -1 -i 1.mp4 -c copy -f rtsp rtsp://127.0.0.1:554/stream
// upstream the video
ffmpeg -re -stream_loop -1 -i "H:\PrivProjects\[2022.03.15] 闸门船舶检测\Delivery\images\test_multiple_right_left_Trim.mp4"  -c copy -f rtsp rtsp://127.0.
1:554/ship
```
![](https://note.youdao.com/yws/api/personal/file/WEB9faff3fd05cb0cbdce9c381c345e2764?method=download&shareKey=c221cea2f5aadbeb51dc61c401d6243b)

## 使用 vlc 打开 rtsp 流
选中媒体，点击打开网络串流
![](https://note.youdao.com/yws/api/personal/file/WEB8b6cb2b181d67e399d0822147fea8eb0?method=download&shareKey=88ac84e88dcacbdf156290fdcd3c2877)

## 相关链接
[FFmpeg 下载链接](https://ffmpeg.org/download.html)  
[EasyDarwin 下载地址](https://github.com/EasyDarwin/EasyDarwin/releases)