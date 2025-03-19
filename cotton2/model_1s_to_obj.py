import struct
import logging
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import math

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

    def _write_vertex(self, obj_file, module_info):
        matrix1 = module_info.get('base_matrix')
        matrix2 = module_info.get('base_matrix_end')
        for i in range(module_info['vertex_num']):
            x, y, z = module_info['vertex'][i]
            if((module_info['name'] == 'seat') | (matrix2 == None)):
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
        for a, b, c, d, e, f, g, h, i, j, material_id in module_info.get('faces', []):
                obj_file.write(f"f {g+1}/{a+1}/ {h+1}/{b+1}/ {i+1}/{c+1}/\n")

    def _create_obj_file(self, module_info):
        """创建OBJ文件并写入基本信息"""
        filename = f"{module_info['name']}_{module_info['id']}.obj"
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

        logging.info(f"Created OBJ file: {filepath}")
        return filepath

    import struct

    def parse_transform_matrix(self, matrix_data):
        """解析15+6的镜像对称参数结构"""
        floats = struct.unpack('<21f', matrix_data)

        base_matrix = floats[:16]  # 4x4矩阵（通常为单位矩阵）
        params_group1 = floats[16:19]  # 参数组1
        params_group2 = floats[19:22]  # 参数组2

        return (base_matrix, params_group1, params_group2)

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
            matrix_data = data[index:index+84]
            base_matrix, params_group1, params_group2 = self.parse_transform_matrix(matrix_data)
            self.current_module_info['base_matrix'] = base_matrix
            self.current_module_info['params_group1'] = params_group1
            self.current_module_info['params_group2'] = params_group2
            index += 84
            index += 50
            if(data[index:index+2] != self.VERTEX_COORDINATES_HEADER):
                logging.debug(f"没找到aa27{index:X}")
            else:
                logging.info(f"当前index 位置: @{index:X}")
                index += 2
                bone_id  = int.from_bytes(data[index:index+2], 'little')
                logging.info(f"骨骼ID:{bone_id }")
                index += 2
                self.current_module_info['bone_id'] = bone_id
                vertex_num = int.from_bytes(data[index:index+2], 'little')
                logging.info(f"当前顶点个数: {vertex_num}")
                index += 4
                # 解析顶点坐标（每个顶点包含x/y/z三个float）
                vertices = []
                self.current_module_info['vertex_num'] = vertex_num
                for _ in range(vertex_num):
                    if index + 12 > len(data):  # 防止越界
                        break
                    x, y, z = struct.unpack_from('<3f', data, index)
                    vertices.append((x, y, z))
                    index += 12  # 每个顶点占12字节
                logging.info(f"当前index 位置: @{index:X}")
                self.current_module_info['vertex'] = vertices

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
                self.current_module_info['normals'] = normals

                second_data_type_num = int.from_bytes(data[index:index+2], 'little')
                logging.info(f"第二段数据数值: {second_data_type_num:X}")
                index += 4
                uv = []
                for num in range(second_data_type_num):
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
                self.current_module_info['uvs'] = uv
                self.current_module_info['uvs_num'] = second_data_type_num
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

            test_index = index + 2
            logging.info(f"结束后内容  {data[test_index:test_index+1]}\n")
            if(b'\x80' == data[test_index:test_index+1]):
                # 解析变换矩阵
                matrix_data = data[index:index+84]
                base_matrix_end, params_group_end1, params_group_end2 = self.parse_transform_matrix(matrix_data)
                self.current_module_info['base_matrix_end'] = base_matrix_end
                self.current_module_info['params_group_end1'] = params_group_end1
                self.current_module_info['params_group_end2'] = params_group_end2
                logging.info(f"第一个矩阵 {(base_matrix, params_group1, params_group2)}\n")
                logging.info(f"第二个矩阵  {(base_matrix_end, params_group_end1, params_group_end2)}\n")

            # 生成OBJ文件
            self._create_obj_file(self.current_module_info)


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