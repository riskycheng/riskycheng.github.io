---
layout: blog
istop: true
title: "船闸船舶危险区域监测"
background-image: http://tva1.sinaimg.cn/large/6b260656gy1h2g27squ4rj217r0k7kfe.jpg
date:  2022-04-14 15:45:56
category: privProjects
tags:
- Nanodet
- libcurl
- openVINO
- ncnn
- Vulkan
---

船舶检测及危险警戒线状态预警。
支持基于OpenVINO，NCNN-Vulkan推理加速，支持RTSP流输入。

# 需求背景
## 难点
针对船舶通过船闸的场景，当船舶通过前，需要打开闸门，同时会形成一定范围的警戒区域，如果船舶在闸门未完全打开的情况下进入警戒区则会引发危险，因此需要针对该场景进行智能监控。  
传统方案中，需要借助单线激光雷达进行侦测，虽然其具备不受环境光照影响的优点，但是由于雨雪天气、湖面杂物、非目标船只的通行等，因为单线雷达并不具备目标检测理解的能力，所以在实际使用中误报率过高，导致系统较难推行。 
## 诉求
低成本、高可靠性可以克服在不同天气状态（光照因素、雨雪天气等），迎广、逆光、折射、湖面倒影、垃圾等干扰情形下工作，并且能对接已有报警系统具备网络通讯能力。

# 解决方案
通过基于深度学习的计算机视觉方案融入目标检测理解：  
- **阶段-1：实时检测目标船只位置**
- **阶段-2：支持警戒区域自定义及RTSP实时流**
- **阶段-3：通过HTTP网络协议进行实时数据回传**

## **阶段-1** 技术要点
### **自训练检测模型**
针对该视场下不同时刻的视频数据进行人工标注、自定义深度学习模型训练，实现能够克服不同光照、角度、大小、距离、形状、运动速度等目标船只的精准定位。
### **检测模型部署**
对于训练好的模型，通过基于两种方式进行加速部署：
###### **针对具备NVIDIA显卡设备**
采用基于NCNN + Vulkan进行部署，在i5-10400F + RTX3060上达到15ms/帧的推理速度 （未量化）
###### **针对Intel纯CPU设备**
采用基于Intel OpenVINO进行部署，在i5-10400F 上达到7ms/帧的推理速度 （未量化，不含核显，否则会更快）
### **算法架构**
![Picture.png](http://tva1.sinaimg.cn/large/6b260656gy1h2g22cub87j20ti0c8n0x.jpg)

## **阶段-2** 技术要点
### **支持外部json配置**  

支持基于json外部配置，包括：

- 多边形警戒区域定义
- 是否启用GPU加速
- 配置远程RTSP流地址
- 本地相机地址
- 检测目标置信度阈值
- 防误报增稳窗口及阈值

配置文件:  
```
{
  "detector": {
    "det_conf_thresh": 0.4,
    "use_GPU": true
  },

  "application": {
    "camera_related": {
      "cameraID": 1234,
      "sourceMode": 2,
      "sourceLocation": "rtsp://admin:abcd1234@182.49.1.11:554/Streaming/Channels/101"
    },
	
    "dangerous_region": {
      "x1": 500,
      "y1": 0,
      "x2": 700,
      "y2": 0,
      "x3": 300,
      "y3": 1080,
      "x4": 100,
      "y4": 1080
    },
    
    "thresh_overlap_px": 10,
    "min_continousOverlapCount": 10,
    "detect_cycle": 1,
    "num_threads": 8,
    "remote_url": "http://shanghai.test.com:8005/Info/cameraInfo"
  }
}
```

### **RTSP实时流解析**
支持基于libVLC的实时流解析，兼容市面上各厂商的网络摄像机，支持RTSP、HTTP、RTMP等多重格式。

### **流程架构**
![Picture2.png](http://tva1.sinaimg.cn/large/6b260656gy1h2g23hubjvj20v40ae77u.jpg)



## **阶段-3** 技术要点
### **支持HTTP协议数据传输** 
将实时检测数据，以json报文方式通过libCurl进行数据回传:  
```
 {                                                              
    "cameraID" : 1234,                                      
    "dangerousRegion" :                                     
    [                                                       
        { "x" : 500, "y" : 0},                                              
        { "x" : 700, "y" : 0},                                    
        { "x" : 500, "y" : 1080}, 
        { "x" : 700, "y" : 1080}
    ],                                                      
    "detectedObjs" :                                        
    [                                                       
        {"conf" : 0.48, "height" : 490, "width" : 69, "x" : 1814, "y" : 490}                                               
    ],                                                      
    "frameID" : 7,                                          
    "isIndanger" : false,                                   
    "timeStamp" : "2022/5/21 15:14:12"                      
}                                                               
```


# 效果演示
![Animation.gif](http://tva1.sinaimg.cn/large/6b260656gy1h2g0ik1zjzg20qq0fvx6p.gif)

# 运行程序
[百度云：可执行程序下载](链接：https://pan.baidu.com/s/1d9bHeCwWUQYBrxA0W9vosg?pwd=h8c0)
## 涉及内容
- **NanoDet 模型模型训练**
- **NanoDet基于NCNN + Vulkan部署**
- **NanoDet基于OpenVINO部署**
- **Jsoncpp用于json解析及回传数据打包**
- **libCurl用于网络接口实现数据回传**
- **libVLC用于接收RTSP/RTMP/HTTP等网络流媒体用于实时检测**
- **OpenCV + FFMPEG 用于本地视频解码**


# 定制合作
可支持需求定制部署，解决实际生产过程中遇到的问题，解放低效人力，高效低成本运作。  
商务合作可联系:
- 电话：17602171768
- 邮箱：3029784716@qq.com