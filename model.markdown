# model.1s 文件解析规范（v1.3更新版）

## 总文件头
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 固定标识 | 6B   | `0xAA4749028C07` 文件头标识 | `FILE_HEADER = b'\xaa\x47\x49\x02\x8c\x07'` |
| 模块个数 | 4B   | 小端格式，总模块数量 | `total_modules = int.from_bytes(data[index:index+4], 'little')` |
| 保留字段 | 8B   | 全零填充（跳过） | `index += 8` |

---

## 模块结构
### 模块头标识
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 固定标识 | 6B   | `0xAA4746042A19` 模块标识 | `MODEL_HEADER = b'\xaa\x47\x46\x04\x2a\x19'` |
| 模块ID | 2B   | 小端格式唯一标识 | `module_id = int.from_bytes(data[index:index+2], 'little')` |
| 名称长度 | 2B   | UTF-16字符数 | `name_len = int.from_bytes(data[index:index+2], 'little')` |
| 模块名称 | (N+1)*2B | UTF-16LE编码，带2B终止符 | `module_name = data[index:index+2+name_len*2].decode('utf-16le')` |

---

### 变换矩阵结构（新增）
| 数据内容 | 长度 | 详细说明 | 对应代码逻辑 |
|---------|------|---------|-------------|
| 矩阵数据 | 84B  | 21个float小端格式 | `base_matrix, p1, p2 = struct.unpack('<21f', matrix_data)` |
| **组成** |       | - 前16个float：4x4基础矩阵<br>- 后续参数组：对称参数 | `self.current_module_info['base_matrix']`<br>`self.current_module_info['params_group1']` |

---

### 顶点数据段（增强说明）
| 新增字段 | 处理逻辑 |
|---------|----------|
| 骨骼ID | `bone_id = int.from_bytes(data[index:index+2], 'little')`<br>关联顶点权重数据 |
| 双矩阵变换 | 动态模块应用两级矩阵变换：<br>```python<br>new_x = (x * rm1[0][0] + ...) + tm1[9]<br>new_x = (new_x1 * rm2[0][0] + ...) + tm2[9]``` |

---

### UV数据段修正
| 变更点 | 说明 |
|-------|------|
| 解析长度 | UV记录数从4B小端读取：<br>`uv_count = int.from_bytes(data[index:index+4], 'little')` |
| 索引偏移 | 面数据UV索引直接使用`a,b,c`字段：<br>`f {g+1}/{a+1}/...` |

---

### 面数据段规范
| 新增特性 | 代码实现 |
|---------|----------|
| 面记录长度 | 每组20B（10个2B索引）<br>`a,b,c,d,e,f,g,h,i,j = struct.unpack('<10H', data)` |
| 材质绑定 | `material_id`动态生成：<br>`faces.append(..., material_id=num)` |

---

## 新增关键处理逻辑
### 1. 双矩阵顶点变换
```python
# 动态模型（如车轮）应用两级矩阵
if module_name != 'seat' and base_matrix_end存在:
    # 第一级矩阵旋转平移
    x_rot1 = x*rm1[0][0] + y*rm1[0][1] + z*rm1[0][2]
    new_x1 = x_rot1 + tm1[9]
    # 第二级矩阵旋转平移
    new_x = new_x1*rm2[0][0] + ... + tm2[9]
```

### 2. 子模块递归解析
```python
# 检测子模块标记
has_submodule = int.from_bytes(data[index:index+2], 'little')
if has_submodule:
    self.process_module(data, index+2, is_base_module=True)
```

---

## 数据验证更新
### 面数据示例
代码输出格式：
```obj
f 33/1/ 46/2/ 79/3/
```
对应原始数据：
- `g=32, h=45, i=78`（索引+1）
- `a=0, b=1, c=2`（UV索引+1）

---

## 文档同步声明
> 本规范与`model_1s_to_obj.py` v1.3完全同步，新增双矩阵变换、子模块递归解析、动态材质绑定等特性。关键更新包括：
> 1. 文件头长度修正（模块个数4B→原文档错误描述为2B）
> 2. 新增双矩阵变换计算规范
> 3. UV段长度解析从2B→4B
> 4. 新增骨骼ID字段及面数据材质绑定逻辑
> 5. 补充子模块递归处理流程

---

## 附录：字段定位标识
| 关键标记 | 十六进制值 | 代码常量 |
|---------|------------|----------|
| 文件头   | AA4749028C07 | `FILE_HEADER` |
| 模块头   | AA4746042A19 | `MODEL_HEADER` |
| 顶点数据头 | AA27       | `VERTEX_COORDINATES_HEADER` |