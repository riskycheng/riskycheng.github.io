from PIL import Image
import os

def resize_image(image_path):
    # 打开图片
    with Image.open(image_path) as img:
        # 获取原始尺寸
        width, height = img.size
        # 计算新尺寸
        new_width = width // 4
        new_height = height // 4
        
        # 调整大小，使用 LANCZOS (高质量) 重采样
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 保存图片，覆盖原文件
        resized_img.save(image_path, quality=95, optimize=True)
        print(f"已处理: {image_path} - 新尺寸: {new_width}x{new_height}")

def main():
    # 图片目录路径
    directory = "images/posts/2024-12-26-iReader"
    
    # 支持的图片格式
    image_extensions = ('.png', '.jpg', '.jpeg')
    
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(directory, filename)
            try:
                resize_image(image_path)
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

if __name__ == "__main__":
    main() 