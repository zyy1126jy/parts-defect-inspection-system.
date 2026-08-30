# parts‑defect‑inspection‑system
汽车零部件缺陷检测系统

## 数据准备阶段
1.数据集来源：Kolektor‑SDD2金属表面缺陷数据集，阿里魔搭社区公开工业缺陷数据集
数据集下载地址：https://www.modelscope.cn/datasets/OpenDataLab/KolektorSDD2/summary
说明：数据集图片体积大，原始图像不上传仓库，访问上方链接获取原始数据。

2.数据预处理：完成图像缩放、灰度转换，编写preprocess.py预处理脚本，输出224*224规格处理后图像。预处理程序存放于 ./data/preprocess.py。

3.AI工具提示词追溯记录：本项目AI交流记录文件存放于 ./prompt/ai_record.json，后续各阶段将持续更新记录。
