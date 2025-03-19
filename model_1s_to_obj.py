import struct
import logging
import os
import shutil
import sys
from tkinter import Tk,filedialog
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

mtl_content = """
# 定义材质
newmtl my_textured_material
Ns 10.0000
Ka 1.0000 1.0000 1.0000
Kd 0.8000 0.8000 0.8000
Ks 0.5000 0.5000 0.5000
Ke 0.0000 0.0000 0.0000
Ni 1.0000
d 1.0000
illum 2

# 引用纹理文件
map_Kd 1.png
map_Ks 0.png
"""


@dataclass
class module:
    id: int = 0
    name: str = ""
    sub_id: int = 0
    sub_name: str = ""
    matrix: list = field(default_factory=list)
    vertex_num: int = 0
    vertex: list = field(default_factory=list)
    uvs_num: int = 0
    uvs: list = field(default_factory=list)
    base_matrix: list = field(default_factory=list)
    base_params_group1: list = field(default_factory=list)
    base_params_group2: list = field(default_factory=list)
    bone_id: int = 0
    normals: list = field(default_factory=list)
    faces_num: int = 0
    sub_matrix: list = field(default_factory=list)
    sub_params_group1: list = field(default_factory=list)
    sub_params_group2: list = field(default_factory=list)
    faces: list = field(default_factory = list)

class Model1SToOBJ:
    # 文件头标识
    MODEL_HEADER =          b'\xaa\x47\x46\x04\x2a\x19'
    FILE_HEADER =           b'\xaa\x47\x49\x02\x8c\x07'
    BASE_MODEL_HEADER =     b'\xaa\x47\x3c\x03\x07\x0e'
    VERTEX_COORDINATES_HEADER = b'\xaa\x27'
    module_list = field(default_factory=module)

    def __init__(self):
        self.output_dir = ""

    def _write_obj_header(self, obj_file, module_info):
        """写入OBJ文件头信息"""
        obj_file.write(f"# Model 1S Conversion Tool\n")
        obj_file.write(f"# Generated at {datetime.now().isoformat()}\n")
        obj_file.write(f"# Module ID: {module_info.id}\n")
        obj_file.write(f"# Module Name: {module_info.name}\n")
        obj_file.write("# Transformation Matrix:\n")

    def _write_vertex(self, obj_file, module_info: module):
        matrix1 = module_info.base_matrix
        matrix2 = module_info.sub_matrix
        for i in range(module_info.vertex_num):
            x, y, z = module_info.vertex[i]
            if((module_info.name == 'seat') | (matrix2 == None)):
                obj_file.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            else:
                rotation_matrix1 = [
                    [matrix1[0], matrix1[1], matrix1[2]],   # 第一行
                    [matrix1[3], matrix1[4], matrix1[5]],   # 第二行
                    [matrix1[6], matrix1[7], matrix1[8]]    # 第三行
                ]
                rotation_matrix2 = [
                    [matrix2[0], matrix2[1], matrix2[2]],   # 第一行
                    [matrix2[3], matrix2[4], matrix2[5]],   # 第二行
                    [matrix2[6], matrix2[7], matrix2[8]]    # 第三行
                ]
                x_rot1 = x * rotation_matrix1[0][0] + y * rotation_matrix1[0][1] + z * rotation_matrix1[0][2]
                y_rot1 = x * rotation_matrix1[1][0] + y * rotation_matrix1[1][1] + z * rotation_matrix1[1][2]
                z_rot1 = x * rotation_matrix1[2][0] + y * rotation_matrix1[2][1] + z * rotation_matrix1[2][2]

                new_x1 = x_rot1 + matrix1[9]
                new_y1 = y_rot1 + matrix1[10]
                new_z1 = z_rot1 + matrix1[11]


                x_rot2 = new_x1 * rotation_matrix2[0][0] + new_y1 * rotation_matrix2[0][1] + new_z1 * rotation_matrix2[0][2]
                y_rot2 = new_x1 * rotation_matrix2[1][0] + new_y1 * rotation_matrix2[1][1] + new_z1 * rotation_matrix2[1][2]
                z_rot2 = new_x1 * rotation_matrix2[2][0] + new_y1 * rotation_matrix2[2][1] + new_z1 * rotation_matrix2[2][2]

                new_x = x_rot2 + matrix2[9]
                new_y = y_rot2 + matrix2[10]
                new_z = z_rot2 + matrix2[11]
                # obj_file.write(f"v {new_x:.6f} {new_y:.6f} {new_z:.6f}\n")
                obj_file.write(f"v {new_x:.6f} {new_y:.6f} {new_z:.6f}\n")

    def _write_uv(self, obj_file, module_info: module):
        """写入UV坐标"""
        if(module_info.uvs == None) :
            obj_file.write("# this module not have uvs\n")
            return
        for uv in module_info.uvs:
            obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

    def _write_normal(self, obj_file, module_info: module):
        """写入法线"""
        if(module_info.normals == None) :
            obj_file.write("# this module not have normals\n")
            return
        for nx, ny, nz in module_info.normals:
            obj_file.write(f"vn {nx:.6f} {ny:.6f} {nz:.6f}\n")

    def _write_faces(self, obj_file, module_info: module):
        """写入面片"""
        if(module_info.faces == None) :
            obj_file.write("# this module not have faces\n")
            return
        for a, b, c, d, e, f, g, h, i, j, material_id in module_info.faces:
                obj_file.write(f"f {g+1}/{a+1}/ {h+1}/{b+1}/ {i+1}/{c+1}/\n")

    def _create_obj_file(self, module_info: module):
        """创建OBJ文件并写入基本信息"""
        filename = f"{module_info.name}_{module_info.id}.obj"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as obj_file:
            self._write_obj_header(obj_file, module_info)
            obj_file.write("\n# Vertex data will be added here\n")
            obj_file.write("\nmtllib test.mtl\n")
            self._write_vertex(obj_file, module_info)
            self._write_uv(obj_file, module_info)
            self._write_normal(obj_file, module_info)
            obj_file.write("\nusemtl my_textured_material\n")
            self._write_faces(obj_file, module_info)

        logging.debug(f"Created OBJ file: {filepath}")
        return filepath

    def _create_mtl_file(self, file_name):
        """创建OBJ文件并写入基本信息"""
        filename = f"test.mtl"
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as obj_file:
                obj_file.write(mtl_content)
            logging.info(f"生成mtl_file ok")
        except Exception as e:
            logging.error(f"生成mtl_file 出错error:{e}")
        return filepath

    def parse_transform_matrix(self, matrix_data):
        """解析15+6的镜像对称参数结构"""
        floats = struct.unpack('<21f', matrix_data)

        base_matrix = floats[:16]  # 4x4矩阵（通常为单位矩阵）
        base_params_group1 = floats[16:19]  # 参数组1
        base_params_group2 = floats[19:22]  # 参数组2

        return (base_matrix, base_params_group1, base_params_group2)

    def process_module(self, data, index, is_sub_module=False, back_module = None):
        if(back_module == None) :
            back_module = module()
        """处理单个模块"""
        start_offset = index
        index += len(self.MODEL_HEADER)

        # 解析模块基本信息
        module_id = int.from_bytes(data[index:index+2], 'little')
        logging.debug(f"当前模块id: {module_id}")
        index += 2
        logging.debug(f"当前index: {index:x}")
        name_len = int.from_bytes(data[index:index+2], 'little')
        index += 2
        module_name = data[index:index+2+name_len*2].decode('utf-16le').strip('\x00')
        index += 2 + name_len*2
        logging.debug(f"当前模块名: {module_name}")
        if(is_sub_module) :
            back_module.sub_id = module_id
            back_module.sub_name = module_name
        else:
            back_module.id = module_id
            back_module.name = module_name
        # 处理子模块标记
        has_submodule = int.from_bytes(data[index:index+2], 'little')
        index += 2

        if has_submodule:
            logging.debug(f"Module {module_id} has submodules, entering recursion...")
            index = self.process_module(data, index+2, True, back_module)
        else:
            index += 2  # 跳过未知字段

            # 解析变换矩阵
            matrix_data = data[index:index+84]
            base_matrix, base_params_group1, base_params_group2 = self.parse_transform_matrix(matrix_data)
            back_module.base_matrix = base_matrix
            back_module.base_params_group1 = base_params_group1
            back_module.base_params_group2 = base_params_group2
            index += 84
            index += 50
            if(data[index:index+2] != self.VERTEX_COORDINATES_HEADER):
                logging.debug(f"没找到aa27{index:X}")
            else:
                logging.debug(f"当前index 位置: @{index:X}")
                index += 2
                bone_id  = int.from_bytes(data[index:index+2], 'little')
                logging.debug(f"骨骼ID:{bone_id }")
                index += 2
                back_module.bone_id = bone_id
                vertex_num = int.from_bytes(data[index:index+2], 'little')
                logging.debug(f"当前顶点个数: {vertex_num}")
                index += 4
                # 解析顶点坐标（每个顶点包含x/y/z三个float）
                vertices = []
                back_module.vertex_num = vertex_num
                for _ in range(vertex_num):
                    if index + 12 > len(data):  # 防止越界
                        break
                    x, y, z = struct.unpack_from('<3f', data, index)
                    vertices.append((x, y, z))
                    index += 12  # 每个顶点占12字节
                logging.debug(f"当前index 位置: @{index:X}")
                back_module.vertex = vertices
                back_module.vertex_num = vertex_num
                uv_count = int.from_bytes(data[index:index+4], 'little')
                index +=4
                normals = []
                for _ in range(uv_count):
                    # 解析3个float（UV + 权重或其他）
                    nx = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    ny = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    nz = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    normals.append((nx, ny, nz))
                back_module.normals = normals
                uvs_num = int.from_bytes(data[index:index+2], 'little')
                logging.debug(f"第二段数据数值: {uvs_num:X}")
                index += 4
                uv = []
                for num in range(uvs_num):
                    vertex_id  = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    tex_block  = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    u = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    v = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    v = 1.0 - v
                    uv.append((u,v))

                back_module.uvs = uv
                back_module.uvs_num = uvs_num
                face_count = int.from_bytes(data[index:index+2], 'little')
                index +=4
                logging.debug(f"当前face_count: @{face_count:X}")
                logging.debug(f"当前index 位置: @{index:X}")
                faces = []
                for num in range(face_count):
                    a = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    b = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    c = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    d = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    e = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    f = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    g = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    h = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    i = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    j = int.from_bytes(data[index:index+2], 'little')
                    index +=2
                    material_id = num
                    faces.append((a, b, c, d, e, f, g, h, i, j, material_id))
                back_module.faces = faces
                back_module.faces_num = face_count

                logging.debug(f"当前index 位置: @{index:X}")

            if(is_sub_module):
                # 解析变换矩阵
                matrix_data = data[index:index+84]
                sub_matrix, sub_params_group1, sub_params_group2 = self.parse_transform_matrix(matrix_data)

                back_module.sub_matrix = sub_matrix
                back_module.sub_params_group1 = sub_params_group1
                back_module.sub_params_group2 = sub_params_group2

                index += 84
                index += 46
            logging.debug(f"end当前index 位置: @{index:X}")

        return index

    def convert(self, input_path, output_dir):
        """主转换函数"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logging.debug(f"\n{'='*40}")
        logging.debug(f"Processing: {input_path}")
        logging.debug(f"Output Directory: {output_dir}")
        logging.debug(f"{'='*40}\n")
        module_list = []
        with open(input_path, 'rb') as f:
            data = f.read()

        index = 0
        total_modules = 0

        try:
            while index < len(data):
                # 检测文件头
                if data[index:index+6] == self.FILE_HEADER:
                    index += 12
                    total_modules = int.from_bytes(data[index:index+4], 'little')
                    logging.debug(f"Total modules declared: {total_modules}")
                    index += 4
                    model_obj = module()
                    logging.debug(f"begin1当前index 位置: @{index:X}")
                    logging.debug(f"index 前数值: {data[index - 4:index]}")

                    index = self.process_module(data, index, back_module=model_obj)
                    #logging.debug(f"model_obj:{model_obj}")
                    self._create_obj_file(model_obj)
                    module_list.append(model_obj)
                    total_modules -= 1

                elif data[index:index+6] == self.BASE_MODEL_HEADER:
                    logging.debug(f"begin2当前index 位置: @{index:X}")
                    logging.debug(f"index 前数值: {data[index - 4:index]}")
                    model_obj = module()
                    index = self.process_module(data, index, False, model_obj)
                    #logging.debug(f"model_obj:{model_obj}")
                    self._create_obj_file(model_obj)
                    module_list.append(model_obj)
                    total_modules -= 1
                else:
                    index += 1
            self._create_mtl_file(file_name="test")
        except Exception as e:
            logging.error(f"Error at offset 0x{index:X}: {str(e)}")
            raise
        self.module_list = module_list
        logging.debug(f"\n{'='*40}")
        logging.debug(f"Conversion completed!")
        logging.debug(f"Processed modules: {abs(total_modules)}")
        logging.debug(f"{'='*40}")
        self.state_print()

    def state_print(self):
        if(self.module_list == None):
            logging.info(f"还未收录module")
        else :
            for now_module in self.module_list:
                logging.info(f"module_name: {now_module.name},id: {now_module.id}")

if __name__ == "__main__":
    # 日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler('conversion.log'),
            logging.StreamHandler()
        ]
    )

    root = Tk()
    root.withdraw()



    if len(sys.argv) < 2:
        source_dir = filedialog.askdirectory(title="选择源目录")
    else:
        source_dir = sys.argv[1]
        print(f"目标目录{source_dir}")
        source_dir = os.path.abspath(source_dir)
        print(f"目标目录{source_dir}")
        if not os.path.exists(source_dir):
            print(f"目标目录不存在{sys.argv[1]}")
            sys.exit(1)

    output_name = os.path.basename(source_dir) + "_module"
    output_path = os.path.join(source_dir, output_name)
    if not os.path.exists(output_path):
        os.makedirs(output_path)


    converter = Model1SToOBJ()

    file_names = ["0.png", "1.png"]

    file_find = True
    model_1s_file_path = ""

    for file_name in file_names:
        file_path = os.path.join(source_dir, file_name)
        # 检查文件是否存在
        if os.path.exists(file_path):
            try:
                # 移动文件到目标目录
                shutil.copy(file_path, os.path.join(output_path, file_name))
                print(f"成功将 {file_name} 复制到 {output_path}")
            except Exception as e:
                print(f"复制 {file_name} 时出错: {e}")
        else:
            print(f"{file_name} 在 {source_dir} 中未找到。")
            file_find = False

    file_path = os.path.join(source_dir, "model.1s")
    if os.path.exists(file_path):
        logging.info(f"成功找到model.1s文件")
        model_1s_file_path = file_path
    else:
        logging.info(f"未找到model.1s文件")
        sys.exit(1)

    if(file_find == True) :
        converter.convert(model_1s_file_path, output_path)
