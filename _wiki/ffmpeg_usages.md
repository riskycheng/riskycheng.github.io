---
layout: wiki
title: FFMPEG 常见用法
cate1: Utils
cate2:
description: ffmpeg
keywords: ffmpeg
---

## 概述
A complete, cross-platform solution to record, convert and stream audio and video.

## 常见用法

压缩视频：
```bash
ffmpeg -y -i <input-video-path> -s 640x480 -vcodec libx264 -b 800000 <out-video-path>
```

图片序列转视频：
```bash
ffmpeg -f image2 -i /home/ttwang/images/image%d.jpg  -vcodec libx264 -r 10  tt.mp4
```

重复图片转视频：
```bash
ffmpeg -loop 1 -i .\images_%03d.bmp -c:v libx264 -t 30 -pix_fmt yuv420p output.mp4
```

视频转图片序列：
```bash
ffmpeg -i input.flv -r 30 -f image2 image_%03d.jpg
```

视频去掉音轨：
```bash
ffmpeg -i input_video.avi  -an output_video_no_sound.avi
```

视频修改码率：
```bash
ffmpeg -i input.mp4  -b:v 10000k output4.mp4
```

QDMS使用视频转码:
```bash
ffmpeg.exe -i  inputVideo.mp4  -vf fps=30  outputVideo.mp4
```

视频截取中间片段:
```bash
ffmpeg -ss 00:03:00 -i video.mp4 -to 00:02:00 -c copy cut.mp4
```

视频旋转(顺时针)：

```python
import os

import cv2

rootPath = r"H:\PrivProjects\videos"
videosPath = os.listdir(rootPath)

for path in videosPath:
    fullSrcPath = os.path.join(rootPath, path)
    fullDstPath = os.path.join(rootPath, path.replace('.mp4', '_rotated.avi'))
    video = cv2.VideoCapture(fullSrcPath)
    size = (720, 1280)
    outVideo = cv2.VideoWriter(fullDstPath, cv2.VideoWriter_fourcc('I', '4', '2', '0'), 30, size)

    while True:
        _, frame = video.read()
        if frame is None:
            break
        # rotate image
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        outVideo.write(frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    video.release()
    outVideo.release()
cv2.destroyAllWindows()
```

## 相关链接
[下载链接](https://ffmpeg.org/download.html)