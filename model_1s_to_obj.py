import struct
import logging
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

@dataclass
class model:
    name:str
    matrix:list
    id:int
    vertex_num:int
    vertex:list
    normals_num:int
    normals:list
    weights:list
    faces_num:int
    faces:list

class Model1SToOBJ:
    # 文件头标识
    MODEL_HEADER =          b'\xaa\x47\x46\x04\x2a\x19'
    FILE_HEADER =           b'\xaa\x47\x49\x02\x8c\x07'
    BASE_MODEL_HEADER =     b'\xaa\x47\x3c\x03\x07\x0e'
    VERTEX_COORDINATES_HEADER = b'\xaa\x27'
    def __init__(self):
        self.output_dir = ""
        self.current_module_info = {
            'name': '',
            'matrix': [],
            'id': 0,
            'vertex_num':0,
            'vertex':[],
            'normals_num':0,
            'normals':[],
            'weights':[],
            'faces_num':0,
            'faces':[]
        }

        # 日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[
                logging.FileHandler('conversion.log'),
                logging.StreamHandler()
            ]
        )

    def _write_obj_header(self, obj_file, module_info):
        """写入OBJ文件头信息"""
        obj_file.write(f"# Model 1S Conversion Tool\n")
        obj_file.write(f"# Generated at {datetime.now().isoformat()}\n")
        obj_file.write(f"# Module ID: {module_info['id']}\n")
        obj_file.write(f"# Module Name: {module_info['name']}\n")
        obj_file.write("# Transformation Matrix:\n")

        # 格式化矩阵输出
        matrix = module_info['matrix']
        for i in range(0, 16, 4):
            obj_file.write(f"# [{matrix[i]:.6f}, {matrix[i+1]:.6f}, "
                         f"{matrix[i+2]:.6f}, {matrix[i+3]:.6f}]\n")
        return
    def _write_vertex(self, obj_file, module_info):
        """写入vertex信息"""

        for i in range(module_info['vertex_num']):
            x, y, z = module_info['vertex'][i]
            matrix = module_info['matrix']
            # 矩阵乘法（行主序，假设平移在m[3], m[7], m[11]）
            # new_x = x * matrix[0] + y * matrix[1] + z * matrix[2] + matrix[3]
            # new_y = x * matrix[4] + y * matrix[5] + z * matrix[6] + matrix[7]
            # new_z = x * matrix[8] + y * matrix[9] + z * matrix[10] + matrix[11]
            # obj_file.write(f"v {new_x:.6f} {new_y:.6f} {new_z:.6f}\n")
            obj_file.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

    def _write_uv(self, obj_file, module_info):
        """写入UV坐标"""
        for uv in module_info['uvs']:
            obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

    def _write_normal(self, obj_file, module_info):
        """写入法线"""
        for nx, ny, nz in module_info.get('normals', []):
            obj_file.write(f"vn {nx:.6f} {ny:.6f} {nz:.6f}\n")

    def _write_faces(self, obj_file, module_info):
        """写入面片"""
        # obj_file.write("mtllib textures.mtl\n")  # 引用材质库
        # current_material = -1
        # for a, b, c, material_id in module_info.get('faces', []):
        #     if material_id != current_material:
        #         obj_file.write(f"usemtl material_{material_id}\n")
        #         current_material = material_id
        #     obj_file.write(f"f {a+1}/{a+1}/{a+1} {b+1}/{b+1}/{b+1} {c+1}/{c+1}/{c+1}\n")
        for a, b, c, d, e, f, g, h, i, j, material_id in module_info.get('faces', []):
            # if e != 0xFFFF:
            #     obj_file.write(f"f {a+1} {b+1} {c+1} {d+1}\n")
            # else :
                obj_file.write(f"f {g+1} {h+1} {i+1}\n")
                # obj_file.write(f"f {g+1}/{g+1}/{g+1} {h+1}/{h+1}/{h+1} {i+1}/{i+1}/{i+1}\n")



    def _create_obj_file(self, module_info):
        """创建OBJ文件并写入基本信息"""
        # 生成安全文件名
        # safe_name = "".join(c if c.isalnum() else "_" for c in module_info['name'])
        filename = f"{module_info['name']}_{module_info['id']}.obj"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as obj_file:
            self._write_obj_header(obj_file, module_info)
            obj_file.write("\n# Vertex data will be added here\n")
            obj_file.write("\nmtllib test.mtl\n")
            self._write_vertex(obj_file, module_info)
            #self._write_uv(obj_file, module_info)
            self._write_normal(obj_file, module_info)
            obj_file.write("\nusemtl my_textured_material\n")
            self._write_faces(obj_file, module_info)

        logging.info(f"Created OBJ file: {filepath}")
        return filepath

    def parse_transform_matrix(self, matrix_data):
        """解析4x4变换矩阵"""
        return [struct.unpack_from('<f', matrix_data, i*4)[0]
               for i in range(16)]

    def process_module(self, data, index, is_base_module=False):
        """处理单个模块"""
        start_offset = index
        index += len(self.MODEL_HEADER)

        # 解析模块基本信息
        module_id = int.from_bytes(data[index:index+2], 'little')
        logging.info(f"当前模块id: {module_id}")
        index += 2

        name_len = int.from_bytes(data[index:index+2], 'little')
        index += 2
        module_name = data[index:index+2+name_len*2].decode('utf-16le').strip('\x00')
        index += 2 + name_len*2
        logging.info(f"当前模块名: {module_name}")
        # 存储当前模块信息
        self.current_module_info = {
            'id': module_id,
            'name': module_name,
            'matrix': [],
            'data_type':'',
            'vertex_num':0,
            'vertex':[],
            'uvs_num':0,
            'uvs':[]
        }

        # 处理子模块标记
        has_submodule = int.from_bytes(data[index:index+2], 'little')
        index += 2

        if has_submodule:
            logging.info(f"Module {module_id} has submodules, entering recursion...")
            index = self.process_module(data, index+2, True)
        else:
            index += 2  # 跳过未知字段

            # 解析变换矩阵
            matrix_data = data[index:index+64]
            self.current_module_info['matrix'] = self.parse_transform_matrix(matrix_data)
            logging.info(f"{self.current_module_info['matrix']}")
            index += 64

            index += 70
            if(data[index:index+2] != self.VERTEX_COORDINATES_HEADER):
                logging.debug(f"没找到aa27{index:X}")
            else:
                index += 2
                data_type_num = int.from_bytes(data[index:index+2], 'little')
                # 根据data_type_num奇偶性判断数据类型
                if data_type_num % 2 == 0:
                    # 偶数：每组12字节（3个float）
                    data_type = 'even'
                    logging.info(f"偶数: 骨骼ID:{data_type_num}")
                else:
                    # 奇数：每组16字节（4个float）
                    data_type = 'odd'
                    logging.info(f"奇数: 骨骼ID:{data_type_num}")
                index += 2
                logging.info(f"当前index 位置: @{index:X}")
                vertex_num = int.from_bytes(data[index:index+2], 'little')
                logging.info(f"当前顶点个数: {vertex_num}")
                index += 4
                logging.info(f"当前index 位置: @{index:X}")
                # 解析顶点坐标（每个顶点包含x/y/z三个float）
                vertices = []
                self.current_module_info['vertex_num'] = vertex_num
                for _ in range(vertex_num):
                    if index + 12 > len(data):  # 防止越界
                        break
                    x, y, z = struct.unpack_from('<3f', data, index)
                    vertices.append((x, y, z))
                    index += 12  # 每个顶点占12字节
                    #logging.info(f"顶点坐标: ({x:.4f}, {y:.4f}, {z:.4f}) @0x{index-12:X}")
                logging.info(f"当前index 位置: @{index:X}")
                self.current_module_info['vertex'] = vertices

                uv_count = int.from_bytes(data[index:index+4], 'little')
                index +=4
                logging.info(f"当前index 位置: @{index:X}")
                logging.info(f"uv_count: @{uv_count:X},3:{uv_count*9 + index:X}, 4:{uv_count*12 + index:X}")
                normals = []
                vertex_indices = []
                for _ in range(uv_count):
                    # 解析3个float（UV + 权重或其他）
                    nx = struct.unpack_from('<H', data, index)[0]
                    index +=4
                    ny = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    nz = struct.unpack_from('<f', data, index)[0]
                    index +=4
                    normals.append((nx, ny, nz))
                logging.info(f"当前index 位置: @{index:X}")
                # 存储到模块信息
                self.current_module_info['normals'] = normals
                logging.info(f"当前index 位置: @{index:X}")

                second_data_type_num = int.from_bytes(data[index:index+2], 'little')
                # 根据data_type_num奇偶性判断数据类型
                logging.info(f"第二段数据数值: {second_data_type_num:X}")
                index += 4
                logging.info(f"当前index 位置: @{index:X}")
                index += second_data_type_num * 12
                logging.info(f"跳过第二段数据 位置: @{index:X}")

                face_count = int.from_bytes(data[index:index+2], 'little')
                index +=4
                logging.info(f"当前face_count: @{face_count:X}")
                logging.info(f"当前index 位置: @{index:X}")
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
                self.current_module_info['faces'] = faces
                self.current_module_info['faces_num'] = face_count
                logging.info(f"当前index 位置: @{index:X}")
            # 生成OBJ文件
            self._create_obj_file(self.current_module_info)

            # 调试信息
            logging.debug(f"Processed module at 0x{start_offset:X}")
            logging.debug(f"Final index position: 0x{index:X}")

        return index

    def convert(self, input_path, output_dir):
        """主转换函数"""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logging.info(f"\n{'='*40}")
        logging.info(f"Processing: {input_path}")
        logging.info(f"Output Directory: {output_dir}")
        logging.info(f"{'='*40}\n")

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
                    logging.info(f"Total modules declared: {total_modules}")
                    index += 4

                # 处理模块
                elif data[index:index+6] == self.MODEL_HEADER:
                    index = self.process_module(data, index)
                    total_modules -= 1
                elif data[index:index+6] == self.BASE_MODEL_HEADER:
                    index = self.process_module(data, index, True)
                    total_modules -= 1
                else:
                    index += 1

        except Exception as e:
            logging.error(f"Error at offset 0x{index:X}: {str(e)}")
            raise

        logging.info(f"\n{'='*40}")
        logging.info(f"Conversion completed!")
        logging.info(f"Processed modules: {abs(total_modules)}")
        logging.info(f"{'='*40}")

if __name__ == "__main__":
    converter = Model1SToOBJ()

    # 配置输入输出
    input_file = "model.1s"              # 输入文件路径
    output_directory = "converted_objs"  # 输出目录

    # 执行转换
    converter.convert(input_file, output_directory)