# kartrider_model_1s_to_obj

[English](#Introduction)|[简体中文](#介绍)

## Introduction
This is a tool for converting 1s model files. If you have any problems with this project, you can submit them to this GitHub page. Thanks for using.
1. Currently only vehicle files can be converted
2. At present, only the initial vehicles have been tested, the latest vehicles and the problem of model dislocation
3. The purple transparency of the steering wheel and other facilities has not been done
## Requirment
python3
```python
import os
import sys
import struct
import logging
import shutil

from tkinter import Tk,filedialog
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
```

## How to use
1. python3 model_1s_to_obj.py
    - run this python file
2. Select the sample file directory "practice0" (for the sample model, you can choose other models)
    - Get target directory -> example: practice0
3. Look at the model for the new folder obj in the target directory right here
    - target directory base_name+"_module" -> practice0_module

- If you do not have a model file, you can use the Rho Reader to get the model file

## 介绍
这是一个转换1s模型文件的工具。如果你对这个项目有任何问题，你可以把它们提交到这个GitHub页面。谢谢使用。
1. 目前只能转换车辆文件
2. 目前只测试了最初始的车辆 最新的车辆还有模型错位的问题
3. 方向盘等设施 紫色转透明化处理还没有做
## 环境要求
python3
```python
import os
import sys
import struct
import logging
import shutil

from tkinter import Tk,filedialog
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
```

## 怎样使用
1. python3 model_1s_to_obj.py
    - 运行该python文件
2. 选择示例文件目录 practice0 (用于示例模型, 可以自行选择其他模型)
    - 获取目标目录 -> 示例为: practice0
3. 查看目标目录下的新增文件夹 obj的模型就在这里
    - 目标目录名称+"_module" -> practice0_module

- 如果您没有模型文件，您可以使用Rho Reader来获取模型文件
