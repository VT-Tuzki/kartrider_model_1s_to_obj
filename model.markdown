# model.1s 文件解析规范（更新版）

## 总文件头
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 固定标识 | 6B   | `0xAA4749028C0700` 模型文件标识 | `FILE_HEADER = b'\xaa\x47\x49\x02\x8c\x07'` |
| 未知数据 | 2B   | 保留字段（全零填充） | 未解析，直接跳过 |
| 模块个数 | 2B   | 小端格式，表示总模块数量 | `total_modules = int.from_bytes(data[index:index+4], 'little')` |
| 未知数据 | 4B   | 保留字段（全零填充） | 未解析，直接跳过 |

---

## 模块头结构
### 基础模块头
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 固定标识 | 6B   | `0xAA4746042A19` 模块标识 | `MODEL_HEADER = b'\xaa\x47\x46\x04\x2a\x19'` |
| 模块ID | 2B   | 小端格式，模块唯一标识 | `module_id = int.from_bytes(data[index:index+2], 'little')` |
| 名称长度 | 2B   | 模块名UTF-16字符数 | `name_len = int.from_bytes(data[index:index+2], 'little')` |
| 模块名称 | N*2B | UTF-16编码的模块名 | `module_name = data[index:index+name_len*2].decode('utf-16le')` |
| 变换矩阵 | 64B  | 4x4矩阵（16个float小端） | `matrix = [struct.unpack_from('<f', data, i*4)[0] for i in range(16)]` |
| 顶点坐标头 | 2B   | `0xAA27` 标识 | `VERTEX_COORDINATES_HEADER = b'\xaa\x27'` |

---

### 顶点数据段
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 顶点数量 | 2B   | 小端格式，顶点总数 | `vertex_num = int.from_bytes(data[index:index+2], 'little')` |
| 顶点坐标 | N*12B | 每组12B：`<3f`（x,y,z） | `x, y, z = struct.unpack_from('<3f', data, index)` |

---

### UV数据段（第二段数据）
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| UV记录数 | 2B   | 小端格式 | `second_data_type_num = int.from_bytes(data[index:index+2], 'little')` |
| UV记录 | N*12B | 每组12B：<br>`vertex_id(2B)`<br>`tex_block(2B)`<br>`u(4B float)`<br>`v(4B float)` | 解析逻辑：<br>```python<br>vertex_id = int.from_bytes(data[i:i+2], 'little')<br>tex_block = int.from_bytes(data[i+2:i+4], 'little')<br>u = struct.unpack('<f', data[i+4:i+8])[0]<br>v = struct.unpack('<f', data[i+8:i+12])[0]<br>v = 1.0 - v  # 垂直翻转<br>``` |

---

### 面数据段（第三段数据）
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 面数量 | 2B   | 小端格式 | `face_count = int.from_bytes(data[index:index+2], 'little')` |
| 面记录 | N*20B | 每组20B：<br>`a(2B)`<br>`b(2B)`<br>`c(2B)`<br>`d(2B)`<br>`e(2B)`<br>`f(2B)`<br>`g(2B)`<br>`h(2B)`<br>`i(2B)`<br>`j(2B)` | 关键字段：<br>- `g,h,i`：面顶点索引<br>导出逻辑：<br>```python<br>obj_file.write(f"f {g+1}/{a+1}/ {h+1}/{b+1}/ {i+1}/{c+1}/\n")<br>``` |

---

## 关键处理流程
### 1. UV坐标修正规则
```python
# 垂直翻转适配Blender坐标系
v = 1.0 - v

# 区块处理（示例）
if tex_block == 1:  # 接触面区块
    u = 1.0 - u     # 水平镜像
    u = u * 0.5 + 0.5  # 映射到右半部
else:               # 侧面区块
    u = u * 0.5     # 映射到左半部
```

### 2. 面数据导出规则
```obj
# OBJ面格式（顶点索引/UV索引）
f 32/23/ 45/34/ 78/56/
```

---

## 材质文件规范（.mtl）
```mtl
newmtl wheel_material
map_Kd 0.png       # 基础颜色贴图
map_Bump 1.png     # 法线贴图（必须设为Non-Color）
bump -bm 1.0       # Blender法线强度参数
```

---

## 模块类型区分
| 模块特征 | 静态模型（偶数） | 动态模型（奇数） |
|---------|------------------|------------------|
| 数据段结构 | 无动画数据 | 包含骨骼权重字段 |
| 典型组件 | 车身、座椅 | 车轮、方向盘 |
| 顶点处理 | 直接导出 | 需应用变换矩阵 |

---

## 数据验证示例
### UV数据解析示例
原始HEX：`00 00 00 00 C2 F6 26 3F B8 C5 F0 3E`
解析结果：
- vertex_id = 0
- tex_block = 0
- u = 0.642 → 映射后 0.321
- v = 0.469 → 翻转后 0.531

### 面数据导出示例
原始面记录：`(a=0, b=1, c=2, ..., g=32, h=45, i=78)`
OBJ输出：`f 33/1/ 46/2/ 79/3/`

---

> 注：本规范基于`model_1s_to_obj.py` v1.2版本实现，确保与代码逻辑完全同步
