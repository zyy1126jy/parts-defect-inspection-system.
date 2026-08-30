import cv2
import os

#图像预处理：缩放+灰度化
def image_preprocess(input_path,output_path,size=(224,224)):
    img = cv2.imread(input_path)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray,size)
    cv2.imwrite(output_path,resized)
    print("图片预处理完成")

if __name__ == "__main__":
    print("预处理脚本就绪")
