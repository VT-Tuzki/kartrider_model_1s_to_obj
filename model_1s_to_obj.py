'''
MIT License

Copyright (c) 2025 VT-Tuzki

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import struct
import logging
import os
import shutil
import sys
from tkinter import Tk,filedialog
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from PIL import Image

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

    def convert_magenta_to_transparent(self, input_path, output_path):
        """将图像中的洋红色(255,0,255)转换为透明"""
        try:
            # 打开图像并转换为RGBA模式
            img = Image.open(input_path).convert("RGBA")
            data = img.getdata()

            # 创建新的像素数据
            new_data = []
            for item in data:
                # 检查是否为洋红色(255,0,255)
                if item[0] > 250 and item[1] < 5 and item[2] > 250:
                    # 设置为完全透明
                    new_data.append((0, 0, 0, 0))
                else:
                    # 保持原样
                    new_data.append(item)

            # 更新图像数据
            img.putdata(new_data)
            img.save(output_path, "PNG")
            logging.info(f"成功将 {input_path} 的洋红色转换为透明")
            return True
        except Exception as e:
            logging.error(f"转换洋红色失败: {e}")
            return False


    def _read_int16(self, data, index):
        """Read a 16-bit integer from data at given index."""
        value = int.from_bytes(data[index:index+2], 'little')
        return value, index + 2

    def _read_int32(self, data, index):
        """Read a 32-bit integer from data at given index."""
        value = int.from_bytes(data[index:index+4], 'little')
        return value, index + 4

    def _read_float(self, data, index):
        """Read a single precision float from data at given index."""
        value = struct.unpack_from('<f', data, index)[0]
        return value, index + 4

    def _read_string(self, data, index):
        """Read a UTF-16LE string from data at given index."""
        # First read the string length
        length, index = self._read_int16(data, index)
        # Then read the string data (including null terminator)
        string_data = data[index:index+2+length*2].decode('utf-16le').strip('\x00')
        return string_data, index + 2 + length*2

    def _read_vertex(self, data, index):
        """Read a vertex (3 floats) from data."""
        x, index = self._read_float(data, index)
        y, index = self._read_float(data, index)
        z, index = self._read_float(data, index)
        return (x, y, z), index

    def process_module(self, data, index, is_sub_module=False, back_module=None):
        """
        Process a single module from the binary data.

        Args:
            data: Binary data containing the module
            index: Current position in the data
            is_sub_module: Whether this is a submodule
            back_module: Module object to populate (created if None)

        Returns:
            Updated index after processing the module
        """
        # Initialize module if not provided
        if back_module is None:
            back_module = module()

        # Skip header
        start_offset = index
        index += len(self.MODEL_HEADER)

        # Parse module basic information
        try:
            # Read module ID
            module_id, index = self._read_int16(data, index)
            logging.debug(f"当前模块id: {module_id}")

            # Read module name
            module_name, index = self._read_string(data, index)
            logging.debug(f"当前模块名: {module_name}")

            # Assign ID and name based on whether this is a submodule
            if is_sub_module:
                back_module.sub_id = module_id
                back_module.sub_name = module_name
            else:
                back_module.id = module_id
                back_module.name = module_name

            # Check if this module has submodules
            has_submodule, index = self._read_int16(data, index)

            if has_submodule:
                logging.debug(f"Module {module_id} has submodules, entering recursion...")
                # Skip 2 bytes and process the submodule
                index = self.process_module(data, index+2, True, back_module)
            else:
                # Skip 2 unknown bytes
                index += 2

                # Parse transformation matrix (84 bytes)
                matrix_data = data[index:index+84]
                base_matrix, base_params_group1, base_params_group2 = self.parse_transform_matrix(matrix_data)
                back_module.base_matrix = base_matrix
                back_module.base_params_group1 = base_params_group1
                back_module.base_params_group2 = base_params_group2
                index += 84
                index += 50  # Skip unknown data

                # Look for vertex coordinate header
                if data[index:index+2] != self.VERTEX_COORDINATES_HEADER:
                    logging.debug(f"没找到顶点坐标头标识 (0xAA27) at offset 0x{index:X}")
                else:
                    logging.debug(f"找到顶点坐标头标识 at offset 0x{index:X}")
                    index += 2

                    # Process geometry data
                    # Read bone ID
                    bone_id, index = self._read_int16(data, index)
                    back_module.bone_id = bone_id
                    logging.debug(f"骨骼ID: {bone_id}")

                    # Read vertex count
                    vertex_count, index = self._read_int16(data, index)
                    back_module.vertex_num = vertex_count
                    logging.debug(f"顶点数量: {vertex_count}")
                    index += 2  # Skip unknown 2 bytes

                    # Read vertices
                    vertices = []
                    for _ in range(vertex_count):
                        if index + 12 > len(data):  # Prevent out of bounds
                            logging.warning(f"顶点数据不完整，已到达数据末尾")
                            break
                        vertex, index = self._read_vertex(data, index)
                        vertices.append(vertex)
                    back_module.vertex = vertices

                    # Read normals
                    normal_count, index = self._read_int32(data, index)
                    normals = []
                    for _ in range(normal_count):
                        normal, index = self._read_vertex(data, index)
                        normals.append(normal)
                    back_module.normals = normals

                    # Read UV coordinates
                    uv_count, index = self._read_int16(data, index)
                    logging.debug(f"UV坐标数量: {uv_count}")
                    index += 2  # Skip unknown 2 bytes

                    uvs = []
                    for _ in range(uv_count):
                        # Read vertex and texture block IDs
                        vertex_id, index = self._read_int16(data, index)
                        tex_block, index = self._read_int16(data, index)

                        # Read U and V coordinates
                        u, index = self._read_float(data, index)
                        v, index = self._read_float(data, index)
                        v = 1.0 - v  # Flip V coordinate (OpenGL -> DirectX convention)

                        uvs.append((u, v))

                    back_module.uvs = uvs
                    back_module.uvs_num = uv_count

                    # Read faces
                    face_count, index = self._read_int16(data, index)
                    logging.debug(f"面片数量: {face_count}")
                    index += 2  # Skip unknown 2 bytes

                    faces = []
                    for face_idx in range(face_count):
                        # Each face has 10 indices (possibly some are UVs, normals, etc.)
                        indices = []
                        for _ in range(10):
                            idx, index = self._read_int16(data, index)
                            indices.append(idx)

                        # Use face index as material ID
                        material_id = face_idx
                        faces.append(tuple(indices + [material_id]))

                    back_module.faces = faces
                    back_module.faces_num = face_count

                # For submodules, read additional transformation matrices
                if is_sub_module:
                    matrix_data = data[index:index+84]
                    sub_matrix, sub_params_group1, sub_params_group2 = self.parse_transform_matrix(matrix_data)

                    back_module.sub_matrix = sub_matrix
                    back_module.sub_params_group1 = sub_params_group1
                    back_module.sub_params_group2 = sub_params_group2

                    index += 84
                    index += 46  # Skip unknown data

            logging.debug(f"完成处理模块 {module_name} (ID: {module_id}) at offset 0x{index:X}")

        except Exception as e:
            logging.error(f"处理模块时出错 at offset 0x{index:X}: {str(e)}")
            # Continue with current index to prevent infinite loops

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

def setup_logging():
    """Configure logging with separate files for debug and info levels."""
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'log')

    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Set up formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create INFO file handler
    info_file = os.path.join(log_dir, f'info_{timestamp}.log')
    info_handler = logging.FileHandler(info_file)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    root_logger.addHandler(info_handler)

    # Create DEBUG file handler
    debug_file = os.path.join(log_dir, f'debug_{timestamp}.log')
    debug_handler = logging.FileHandler(debug_file)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    root_logger.addHandler(debug_handler)

    # Create console handler for INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging initialized. INFO log: {info_file}, DEBUG log: {debug_file}")

def get_source_directory(args):
    """Get source directory from command line arguments or file dialog."""
    if len(args) < 2:
        root = Tk()
        root.withdraw()
        source_dir = filedialog.askdirectory(title="选择源目录")
    else:
        source_dir = args[1]
        print(f"目标目录: {source_dir}")
        source_dir = os.path.abspath(source_dir)
        if not os.path.exists(source_dir):
            print(f"目标目录不存在: {source_dir}")
            sys.exit(1)
    return source_dir

def prepare_output_directory(source_dir):
    """Create output directory based on source directory name."""
    output_name = os.path.basename(source_dir) + "_module"
    output_path = os.path.join(source_dir, output_name)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return output_path

def process_texture_files(source_dir, output_path, converter):
    """Copy and process texture files to output directory."""
    file_names = ["0.png", "1.png"]
    all_files_found = True

    for file_name in file_names:
        file_path = os.path.join(source_dir, file_name)
        if os.path.exists(file_path):
            try:
                output_file_path = os.path.join(output_path, file_name)
                # Convert magenta to transparent for 1.png
                if file_name == "1.png":
                    converter.convert_magenta_to_transparent(file_path, output_file_path)
                    print(f"成功将 {file_name} 处理并保存到 {output_path}，洋红色已转换为透明")
                else:
                    # Just copy other files
                    shutil.copy(file_path, output_file_path)
                    print(f"成功将 {file_name} 复制到 {output_path}")
            except Exception as e:
                print(f"处理 {file_name} 时出错: {e}")
                all_files_found = False
        else:
            print(f"{file_name} 在 {source_dir} 中未找到。")
            all_files_found = False

    return all_files_found

def find_model_file(source_dir):
    """Find and verify the model.1s file exists."""
    file_path = os.path.join(source_dir, "model.1s")
    if os.path.exists(file_path):
        logging.info(f"成功找到model.1s文件")
        return file_path
    else:
        logging.info(f"未找到model.1s文件")
        return None

def main():
    """Main entry point for the application."""
    setup_logging()

    # Get source directory
    source_dir = get_source_directory(sys.argv)

    # Prepare output directory
    output_path = prepare_output_directory(source_dir)

    # Create converter instance
    converter = Model1SToOBJ()

    # Process texture files
    textures_ok = process_texture_files(source_dir, output_path, converter)

    # Find and verify model file
    model_file_path = find_model_file(source_dir)
    if not model_file_path:
        sys.exit(1)

    # Convert model if everything is ready
    if textures_ok:
        converter.convert(model_file_path, output_path)
    else:
        logging.warning("Some texture files were missing or failed to process. Conversion may be incomplete.")
        # Continue with conversion anyway, as the model structure can still be useful
        converter.convert(model_file_path, output_path)

if __name__ == "__main__":
    main()
