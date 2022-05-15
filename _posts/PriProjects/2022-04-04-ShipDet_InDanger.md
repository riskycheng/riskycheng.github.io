---
layout: blog
istop: true
title: "船闸船舶危险区域监测"
background-image: http://ot1cc1u9t.bkt.clouddn.com/17-7-16/38390376.jpg
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

## 需求背景
通过检测器检测特定图标，完成收件人区域的定位，再根据版面相对位置信息，使用OCR结合正则匹配进行文本内容检测与识别，从而实现收件人信息的提取。  
该项目中应用到的技术点：  
- **Nanodet (plus-m_416)检测器实现目标区域检测**
- **ncnn windows上的部署实现NanoDet模型推理**
- **zbar c++部署实现条形码识别**
- **PaddleOCR c++部署实现文本检测识别**

## 效果演示
![image.png](https://note.youdao.com/yws/res/10575/WEBRESOURCE7c2c814150a50e856c8105be15de430c)