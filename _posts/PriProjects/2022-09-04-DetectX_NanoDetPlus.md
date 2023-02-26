---
layout: blog
istop: true
title: "DetectX 深度学习模型Android部署 - NanoDet-Plus + NCNN"
background-image: http://tva1.sinaimg.cn/large/6b260656gy1h5uyxninprj20yh0fddo8.jpg
date:  2022-09-04 14:08:56
category: privProjects
tags:
- Nanodet-Plus
- ncnn
- Vulkan
---

# 需求背景
使用流行的NCNN, DNN， MNN， SNPE， torch_c++ 等框架将主流的Yolo，Nanodet， MobileSSD等模型部署到Android设备上。
## 难点
当前深度学习模型多是使用python进行训练并推理运行，在实验阶段有较高的效率，但是无法直接部署到端侧设备上。并且不同的厂商结合自身硬件优势提供了不同的推理框架，从而也使得部署实现变得复杂。

## 诉求
本文是使用NCNN将Nanodet-Plus_m416部署到android设备上，调用摄像头达到实时检测效果，并根据自身需求训练NanoDet-Plus模型并部署。
# 解决方案
NanoDet-Plus使用NCNN基于C++的实现并部署：  
- **阶段-1：CameraX 获取实时视频流**
- **阶段-2：NCNN实现NanoDet-Plus_m416推理**
- **阶段-3：结果解析并绘制**
- **阶段-4：自训练NanoDet-Plus_m416部署**

## **阶段-1** 技术要点
### **CameraX概述**
Android下的Camera接口从Camera到Camera2，始终比较难用，在最新的CameraX接口中，简化了Camera初始化流程，自动化管理Camera的生命周期，并完全隔离了显示（Preview），计算（Analyzer）和拍摄（Capture). 
### **CameraX主要流程**
##### 继承Analyzer
在Analyzer中实现深度学习模型的计算调用，并将其加入到后续的CameraX的实例中：
```
public class NanodetPlusAnalyzer implements ImageAnalysis.Analyzer {
    private final static String TAG = NanodetPlusAnalyzer.class.getSimpleName();
    private Context mContext;
    private UpdateUICallback mUpdateUICallback;
    private JNIManager mJNIManager;

    // 自定义的UI更新接口，用于异步回调更新UI
    public void setUpdateUICallback(UpdateUICallback updateUICallback) {
        mUpdateUICallback = updateUICallback;
    }

    // 构造函数用于接收模型等参数信息进行深度学习模型初始化 
    public NanodetPlusAnalyzer(@NonNull Context context) {
        mContext = context;
        mJNIManager = JNIManager.getInstance();
        mJNIManager.nanoDet_Init(App.NANODET_PLUS_PARAM_PATH,
                App.NANODET_PLUS_BIN_PATH);
    }
    
    // 在analyze函数中进行深度学习计算分析，可以根据实际需求设计成同步或者异步调用
    @Override
    public void analyze(@NonNull ImageProxy image) {
        // 将YUV转换为RGBA
        Bitmap bitmap = LocalUtils.YUV_420_888_toRGB(mContext, image, image.getWidth(), image.getHeight());

        // 关闭media.Image,否则会阻塞Camera取帧线程
        image.close();
        
        // 调用深度学习模型native接口进行推理计算
        mJNIManager.nanoDet_Detect(bitmap);
        
        // 将结果返回给UI线程进行绘制
        mUpdateUICallback.onAnalysisDone(bitmap);
    }
}
```


##### 初始化Camera实例
```
// 实例化ImageAnalysis
public ImageAnalysis buildAnalyzer(ImageAnalysis.Analyzer analyzer) {
    ImageAnalysis resAnalyzer = new ImageAnalysis.Builder().build();
    Executor imageAnalyzerExecutor = Executors.newSingleThreadExecutor();
    resAnalyzer.setAnalyzer(imageAnalyzerExecutor, analyzer);
    return resAnalyzer;
}

// 将ImageAnalysis绑定到Camera实例中，并绑定所属Activity生命周期
public void setupCamera(ImageAnalysis.Analyzer analyzer) {
        final CameraSelector cameraSelector = new CameraSelector.Builder()
                .requireLensFacing(CameraSelector.LENS_FACING_BACK)
                .build();
        final ListenableFuture cameraProviderFuture = ProcessCameraProvider.getInstance(this);
        cameraProviderFuture.addListener(new Runnable() {
            @Override
            public void run() {
                try {
                    //get camera provider
                    ProcessCameraProvider cameraProvider = (ProcessCameraProvider) cameraProviderFuture.get();

                    //bind to use-cases before rebinding them
                    cameraProvider.unbindAll();
                    mCamera = cameraProvider.bindToLifecycle(
                            MainActivity.this,
                            cameraSelector,
                            buildAnalyzer(analyzer)
                    );
                } catch (Exception e) {
                    Log.e(TAG, "fail to open camera >>> " + e.getMessage());
                }
            }
        }, ContextCompat.getMainExecutor(this));
    }
```

##### UI渲染结果
通过接口来异步更新结果，为了方便，将结果直接绘制到了原图内存中，因此这里的resBitmap就是带有结果的实例。
```
public void onAnalysisDone(Bitmap resBitmap) {
    runOnUiThread(() -> {
        Log.d(TAG, "got result from analyzer...");
        mImageViewDisplay.setImageBitmap(resBitmap);
    });
}
```

## **阶段-2** 技术要点
### **NCNN实现NanoDet-Plus_m416推理**  

#### NanoDet-Plus网络结构
![nanodet-plus-arch.png](https://note.youdao.com/yws/api/personal/file/WEB5a91bfdbd758f4bb3a0d8d9597c91a96?method=download&shareKey=ba98fe8db7c8c125e7a65c0d5d1b9413)

对于部署，不同于上一个版本，默认的模型结构中将之前的3尺度6输出，合并成单个节点输出：
![006C3FgEgy1gxs7a3po8qj30k008sab2.jpg](https://note.youdao.com/yws/api/personal/file/WEB2613a099a4aeef3ce176b9385fc553f3?method=download&shareKey=a53e46da292b64e8d7c4c9e25cfd3cda)

从原作者的git仓库中： [https://github.com/RangiLyu/nanodet/tree/main/demo_ncnn](https://note.youdao.com/)进行封装.  
接口定义 nanodet.h:
```
//
// Create by RangiLyu
// 2020 / 10 / 2
//

#ifndef NANODET_H
#define NANODET_H

#include <opencv2/core/core.hpp>
#include <net.h>

typedef struct HeadInfo
{
    std::string cls_layer;
    std::string dis_layer;
    int stride;
};

struct CenterPrior
{
    int x;
    int y;
    int stride;
};

typedef struct BoxInfo
{
    float x1;
    float y1;
    float x2;
    float y2;
    float score;
    int label;
} BoxInfo;

class NanoDet
{
public:
    NanoDet(const char* param, const char* bin, bool useGPU);

    ~NanoDet();

    static NanoDet* detector;
    ncnn::Net* Net;
    static bool hasGPU;
    // modify these parameters to the same with your config if you want to use your own model
    int input_size[2] = {416, 416}; // input height and width
    int num_class = 80; // number of classes. 80 for COCO
    int reg_max = 7; // `reg_max` set in the training config. Default: 7.
    std::vector<int> strides = { 8, 16, 32, 64 }; // strides of the multi-level feature.

    std::vector<BoxInfo> detect(cv::Mat image, float score_threshold, float nms_threshold);

    std::vector<std::string> labels{ "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
                                     "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
                                     "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
                                     "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
                                     "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
                                     "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
                                     "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
                                     "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
                                     "hair drier", "toothbrush" };
private:
    void preprocess(cv::Mat& image, ncnn::Mat& in);
    void decode_infer(ncnn::Mat& feats, std::vector<CenterPrior>& center_priors, float threshold, std::vector<std::vector<BoxInfo>>& results);
    BoxInfo disPred2Bbox(const float*& dfl_det, int label, float score, int x, int y, int stride);
    static void nms(std::vector<BoxInfo>& result, float nms_threshold);

};

#endif //NANODET_H
```

接口实现 nanodet.cpp:
```
//
// Create by RangiLyu
// 2020 / 10 / 2
//

#include "nanodet.h"
#include <benchmark.h>
// #include <iostream>

inline float fast_exp(float x)
{
    union {
        uint32_t i;
        float f;
    } v{};
    v.i = (1 << 23) * (1.4426950409 * x + 126.93490512f);
    return v.f;
}

inline float sigmoid(float x)
{
    return 1.0f / (1.0f + fast_exp(-x));
}

template<typename _Tp>
int activation_function_softmax(const _Tp* src, _Tp* dst, int length)
{
    const _Tp alpha = *std::max_element(src, src + length);
    _Tp denominator{ 0 };

    for (int i = 0; i < length; ++i) {
        dst[i] = fast_exp(src[i] - alpha);
        denominator += dst[i];
    }

    for (int i = 0; i < length; ++i) {
        dst[i] /= denominator;
    }

    return 0;
}


static void generate_grid_center_priors(const int input_height, const int input_width, std::vector<int>& strides, std::vector<CenterPrior>& center_priors)
{
    for (int i = 0; i < (int)strides.size(); i++)
    {
        int stride = strides[i];
        int feat_w = ceil((float)input_width / stride);
        int feat_h = ceil((float)input_height / stride);
        for (int y = 0; y < feat_h; y++)
        {
            for (int x = 0; x < feat_w; x++)
            {
                CenterPrior ct;
                ct.x = x;
                ct.y = y;
                ct.stride = stride;
                center_priors.push_back(ct);
            }
        }
    }
}


bool NanoDet::hasGPU = false;
NanoDet* NanoDet::detector = nullptr;

NanoDet::NanoDet(const char* param, const char* bin, bool useGPU)
{
    this->Net = new ncnn::Net();
    // opt
#if NCNN_VULKAN
    this->hasGPU = ncnn::get_gpu_count() > 0;
#endif
    this->Net->opt.use_vulkan_compute = false; //hasGPU && useGPU;  // gpu
    this->Net->opt.use_fp16_arithmetic = true;
    this->Net->opt.use_fp16_packed = true;
    this->Net->opt.use_fp16_storage = true;
    this->Net->load_param(param);
    this->Net->load_model(bin);
}

NanoDet::~NanoDet()
{
    delete this->Net;
}

void NanoDet::preprocess(cv::Mat& image, ncnn::Mat& in)
{
    int img_w = image.cols;
    int img_h = image.rows;

    in = ncnn::Mat::from_pixels(image.data, ncnn::Mat::PIXEL_BGR, img_w, img_h);
    //in = ncnn::Mat::from_pixels_resize(image.data, ncnn::Mat::PIXEL_BGR, img_w, img_h, this->input_width, this->input_height);

    const float mean_vals[3] = { 103.53f, 116.28f, 123.675f };
    const float norm_vals[3] = { 0.017429f, 0.017507f, 0.017125f };
    in.substract_mean_normalize(mean_vals, norm_vals);
}

std::vector<BoxInfo> NanoDet::detect(cv::Mat image, float score_threshold, float nms_threshold)
{
    ncnn::Mat input;
    preprocess(image, input);

    //double start = ncnn::get_current_time();

    auto ex = this->Net->create_extractor();
    ex.set_light_mode(false);
    ex.set_num_threads(4);
#if NCNN_VULKAN
    ex.set_vulkan_compute(this->hasGPU);
#endif
    ex.input("data", input);

    std::vector<std::vector<BoxInfo>> results;
    results.resize(this->num_class);

    ncnn::Mat out;
    ex.extract("output", out);
    // printf("%d %d %d \n", out.w, out.h, out.c);

    // generate center priors in format of (x, y, stride)
    std::vector<CenterPrior> center_priors;
    generate_grid_center_priors(this->input_size[0], this->input_size[1], this->strides, center_priors);

    this->decode_infer(out, center_priors, score_threshold, results);

    std::vector<BoxInfo> dets;
    for (int i = 0; i < (int)results.size(); i++)
    {
        this->nms(results[i], nms_threshold);

        for (auto box : results[i])
        {
            dets.push_back(box);
        }
    }

    //double end = ncnn::get_current_time();
    //double time = end - start;
    //printf("Detect Time:%7.2f \n", time);

    return dets;
}

void NanoDet::decode_infer(ncnn::Mat& feats, std::vector<CenterPrior>& center_priors, float threshold, std::vector<std::vector<BoxInfo>>& results)
{
    const int num_points = center_priors.size();
    //printf("num_points:%d\n", num_points);

    //cv::Mat debug_heatmap = cv::Mat(feature_h, feature_w, CV_8UC3);
    for (int idx = 0; idx < num_points; idx++)
    {
        const int ct_x = center_priors[idx].x;
        const int ct_y = center_priors[idx].y;
        const int stride = center_priors[idx].stride;

        const float* scores = feats.row(idx);
        float score = 0;
        int cur_label = 0;
        for (int label = 0; label < this->num_class; label++)
        {
            if (scores[label] > score)
            {
                score = scores[label];
                cur_label = label;
            }
        }
        if (score > threshold)
        {
            //std::cout << "label:" << cur_label << " score:" << score << std::endl;
            const float* bbox_pred = feats.row(idx) + this->num_class;
            results[cur_label].push_back(this->disPred2Bbox(bbox_pred, cur_label, score, ct_x, ct_y, stride));
            //debug_heatmap.at<cv::Vec3b>(row, col)[0] = 255;
            //cv::imshow("debug", debug_heatmap);
        }
    }
}

BoxInfo NanoDet::disPred2Bbox(const float*& dfl_det, int label, float score, int x, int y, int stride)
{
    float ct_x = x * stride;
    float ct_y = y * stride;
    std::vector<float> dis_pred;
    dis_pred.resize(4);
    for (int i = 0; i < 4; i++)
    {
        float dis = 0;
        float* dis_after_sm = new float[this->reg_max + 1];
        activation_function_softmax(dfl_det + i * (this->reg_max + 1), dis_after_sm, this->reg_max + 1);
        for (int j = 0; j < this->reg_max + 1; j++)
        {
            dis += j * dis_after_sm[j];
        }
        dis *= stride;
        //std::cout << "dis:" << dis << std::endl;
        dis_pred[i] = dis;
        delete[] dis_after_sm;
    }
    float xmin = (std::max)(ct_x - dis_pred[0], .0f);
    float ymin = (std::max)(ct_y - dis_pred[1], .0f);
    float xmax = (std::min)(ct_x + dis_pred[2], (float)this->input_size[0]);
    float ymax = (std::min)(ct_y + dis_pred[3], (float)this->input_size[1]);

    //std::cout << xmin << "," << ymin << "," << xmax << "," << xmax << "," << std::endl;
    return BoxInfo { xmin, ymin, xmax, ymax, score, label };
}

void NanoDet::nms(std::vector<BoxInfo>& input_boxes, float NMS_THRESH)
{
    std::sort(input_boxes.begin(), input_boxes.end(), [](BoxInfo a, BoxInfo b) { return a.score > b.score; });
    std::vector<float> vArea(input_boxes.size());
    for (int i = 0; i < int(input_boxes.size()); ++i) {
        vArea[i] = (input_boxes.at(i).x2 - input_boxes.at(i).x1 + 1)
                   * (input_boxes.at(i).y2 - input_boxes.at(i).y1 + 1);
    }
    for (int i = 0; i < int(input_boxes.size()); ++i) {
        for (int j = i + 1; j < int(input_boxes.size());) {
            float xx1 = (std::max)(input_boxes[i].x1, input_boxes[j].x1);
            float yy1 = (std::max)(input_boxes[i].y1, input_boxes[j].y1);
            float xx2 = (std::min)(input_boxes[i].x2, input_boxes[j].x2);
            float yy2 = (std::min)(input_boxes[i].y2, input_boxes[j].y2);
            float w = (std::max)(float(0), xx2 - xx1 + 1);
            float h = (std::max)(float(0), yy2 - yy1 + 1);
            float inter = w * h;
            float ovr = inter / (vArea[i] + vArea[j] - inter);
            if (ovr >= NMS_THRESH) {
                input_boxes.erase(input_boxes.begin() + j);
                vArea.erase(vArea.begin() + j);
            }
            else {
                j++;
            }
        }
    }
}
```


## **阶段-3** 技术要点

### **深度学习native接口**
在JNI层实现以上Nanodet接口的调用，从而完成深度学习模型推理, 并在完成计算后将结果直接绘制到原图的Buffer上：
```
extern "C"
JNIEXPORT void JNICALL
Java_com_fatfish_chengjian_utils_JNIManager_nanoDet_1Init(JNIEnv *env, jobject thiz,
                                                          jstring modelParamPath,
                                                          jstring modelBinPath) {

    LOGI("entering %s", __FUNCTION__);
    const char *paramPath = strdup(env->GetStringUTFChars(modelParamPath, nullptr));
    const char *binPath = strdup(env->GetStringUTFChars(modelBinPath, nullptr));
    LOGI("loading from %s, %s", paramPath, binPath);
    NanoDet::detector = new NanoDet(paramPath, binPath, false);
    LOGI("exiting %s", __FUNCTION__);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_fatfish_chengjian_utils_JNIManager_nanoDet_1Detect(JNIEnv *env, jobject thiz,
                                                            jobject inputBitmap) {
    LOGI("entering %s", __FUNCTION__);
    uint32_t *_inputBitmap;
    AndroidBitmapInfo bmapInfo;
    AndroidBitmap_getInfo(env, inputBitmap, &bmapInfo);
    AndroidBitmap_lockPixels(env, inputBitmap, (void **) &_inputBitmap);
    auto *imagePtr = (uint8_t *) _inputBitmap;

    //get image info
    auto width = bmapInfo.width;
    auto height = bmapInfo.height;

    int model_height = NanoDet::detector->input_size[0];
    int model_width = NanoDet::detector->input_size[1];

    Mat image = Mat((int)height, (int)width, CV_8UC4);
    image.data = imagePtr;

    Mat tmpMat;
    cvtColor(image, tmpMat, COLOR_RGBA2BGR);

    object_rect effect_roi{};
    cv::Mat resized_img;
    resize_uniform(tmpMat, resized_img, cv::Size(model_width, model_height), effect_roi);
    auto results = NanoDet::detector->detect(resized_img, 0.4, 0.5);

    draw_bboxes(image, results, effect_roi);
    AndroidBitmap_unlockPixels(env, inputBitmap);
    tmpMat.release();
    LOGI("exiting %s", __FUNCTION__);
}                                                            
```
其中相关的预处理代码可以参考完整代码地址： [https://github.com/riskycheng/DetectX](https://github.com/riskycheng/DetectX)


## **阶段-4** 技术要点
基于NanoDet-Plus，训练自己的数据集并完成设备端部署。本模型是客户定制模型，包含定位符号和叶片两种目标，其中定位符号用于对容器的位置进行定位并旋转矫正，叶片定位后用于计算面积、轮廓等信息，其中示意图如下所示：
![Screenshot 2022-09-04 234017.png](https://note.youdao.com/yws/api/personal/file/WEB7052944beded38ff66a11747bdc47017?method=download&shareKey=e60d4a90b3a35e515ce924ccf04a2338)


# 效果演示
通用模型演示效果， 备注（在设备上可以做到30帧/s运行速度，此处为了图床加载速度，FPS设置为1）
![2022-09-04-23-26-26.gif](https://note.youdao.com/yws/api/personal/file/WEBe56984beddfe91d2774b5706e844898b?method=download&shareKey=ccad70a6de4a033f8ad12200f06282b1)

自定义模型演示效果， 备注（在设备上可以做到30帧/s运行速度，此处为了图床加载速度，FPS设置为1）
![2022-09-04-23-42-50.gif](https://note.youdao.com/yws/api/personal/file/WEB0a4fd8b916a14c6e87c8be83ad5dcc82?method=download&shareKey=f46f8a39148a0e25a0595791c25af041)

# 运行程序
百度云：[Android APK版本](链接：https://pan.baidu.com/s/1ZZrF9CuJ2YQ0cwuWmtTMCA?pwd=sbpt)
## 涉及内容
- **NanoDetPlus 模型模型训练**
- **NanoDet基于NCNN + Vulkan部署**
- **OpenCV 用于Android版本图像处理**
- **CameraX用于驱动获取相机帧及预览**
- **renderScript用于YUV转成RGBA**

## 源码地址
完整源码带模型文件 求 **Star** ： [https://github.com/riskycheng/DetectX](https://github.com/riskycheng/DetectX)


# 定制合作
可支持需求定制部署，解决实际生产过程中遇到的问题，解放低效人力，高效低成本运作。  
商务合作可联系:
- 电话：17602171768
- 邮箱：3029784716@qq.com