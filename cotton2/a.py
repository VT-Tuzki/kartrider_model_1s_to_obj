import struct
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelModule:
    def __init__(self, start_offset):
        self.start_offset = start_offset
        self.end_offset = start_offset
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.faces = []
        self.materials = []
        self.module_name = "unnamed"
        self.valid = False

def setup_logger():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"convert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )

def read_float(data):
    try:
        return struct.unpack('<f', data)[0]
    except struct.error as e:
        logger.error(f"Float解析错误: {e}")
        raise

def read_uint16(data):
    try:
        return struct.unpack('<H', data)[0]
    except struct.error as e:
        logger.error(f"Uint16解析错误: {e}")
        raise

def read_uint32(data):
    try:
        return struct.unpack('<I', data)[0]
    except struct.error as e:
        logger.error(f"Uint32解析错误: {e}")
        raise

def detect_module_header(data, ptr):
    """动态检测模块头并返回头部长度"""
    headers = {
        b'\x00\xaa\x47\x46\x04\x2a\x19': 8,  # 标准头
        b'\xaa\x47\x46\x04\x2a\x19': 7,     # 无00前缀
        b'\xaa\x47\x49\x02': 4             # 特殊类型头
    }
    for sig, length in headers.items():
        if data[ptr:ptr+len(sig)] == sig:
            return length
    return 0

def parse_vertex_block(data, ptr, count):
    vertices = []
    for _ in range(count):
        if ptr + 16 > len(data):
            raise ValueError("顶点数据不足")
        x = read_float(data[ptr:ptr+4])
        y = read_float(data[ptr+4:ptr+8])
        z = read_float(data[ptr+8:ptr+12])
        vertices.append((x, y, z))
        ptr += 16
    return ptr, vertices

def parse_uv_block(data, ptr):
    if ptr + 4 > len(data):
        return ptr, []

    uv_count = read_uint16(data[ptr:ptr+2])
    ptr += 4  # 跳过YYZZZZ00

    uvs = []
    for _ in range(uv_count):
        if ptr + 8 > len(data):
            break
        u = read_float(data[ptr:ptr+4])
        v = 1.0 - read_float(data[ptr+4:ptr+8])  # 翻转V轴
        uvs.append((u, v))
        ptr += 8
    return ptr, uvs

def parse_faces(data, ptr, face_count):
    """三角带面数据解析"""
    faces = []
    for _ in range(face_count):
        if ptr + 6 > len(data):
            break
        indices = [
            read_uint16(data[ptr:ptr+2]),
            read_uint16(data[ptr+2:ptr+4]),
            read_uint16(data[ptr+4:ptr+6])
        ]
        # 三角带转三角面
        if 0xFFFF not in indices:
            faces.append((indices[0]+1, indices[1]+1, indices[2]+1))
        ptr += 6
    return ptr, faces

def parse_material(data, ptr):
    """解析材质组名称"""
    if ptr + 12 > len(data):
        return ptr, ""

    # 00AA473C03070EKKKKRRRR 结构
    ptr += 12  # 跳过固定头
    name_len = read_uint16(data[ptr:ptr+2]) * 2  # UTF-16长度
    ptr += 2

    if ptr + name_len > len(data):
        return ptr, ""

    name = data[ptr:ptr+name_len].decode('utf-16-le').strip('\x00')
    # 映射已知贴图名称
    if "wheel" in name:
        name = "0.png"
    elif "body" in name:
        name = "1.png"
    elif "shadow" in name:
        name = "shadow.png"

    return ptr + name_len, name

def parse_module(data, ptr):
    header_len = detect_module_header(data, ptr)
    if not header_len:
        return None, ptr

    module = ModelModule(ptr)
    ptr += header_len

    try:
        # 解析顶点数据
        if ptr + 4 > len(data):
            return None, ptr
        vertex_count = read_uint32(data[ptr:ptr+4])
        ptr +=4
        ptr, vertices = parse_vertex_block(data, ptr, vertex_count)
        module.vertices = vertices

        # 解析UV数据
        if ptr + 2 <= len(data) and data[ptr:ptr+2] == b'\x00\xaa':
            ptr +=2
            ptr, uvs = parse_uv_block(data, ptr)
            module.uvs = uvs

        # 解析面数据
        if ptr + 4 <= len(data):
            face_count = read_uint16(data[ptr:ptr+2])
            ptr +=4
            ptr, faces = parse_faces(data, ptr, face_count)
            module.faces = faces

        # 解析材质组名称
        if ptr + 4 <= len(data) and data[ptr:ptr+4] == b'\x00\xaa\x47\x3c':
            ptr, mat_name = parse_material(data, ptr)
            module.materials.append(mat_name)
            module.module_name = mat_name.split('.')[0]  # 去除扩展名

        module.end_offset = ptr
        module.valid = True
        return module, ptr

    except Exception as e:
        logger.error(f"模块解析失败 @{ptr:08X}: {str(e)}")
        return None, ptr

def convert_to_obj(input_path, output_dir):
    setup_logger()

    try:
        with open(input_path, 'rb') as f:
            data = f.read()
        logger.info(f"成功读取文件: {len(data)}字节")
    except Exception as e:
        logger.error(f"文件读取失败: {str(e)}")
        return

    modules = []
    ptr = 0

    while ptr < len(data) - 16:
        try:
            module, new_ptr = parse_module(data, ptr)
            if module and module.valid:
                modules.append(module)
                ptr = new_ptr
                logger.info(f"解析成功: {module.module_name} @{module.start_offset:08X}")
            else:
                ptr +=1
        except Exception as e:
            logger.error(f"主循环错误 @{ptr:08X}: {str(e)}")
            ptr +=1

    # 生成OBJ文件
    os.makedirs(output_dir, exist_ok=True)
    for module in modules:
        if not module.vertices:
            continue

        safe_name = ''.join(c if c.isalnum() else '_' for c in module.module_name)
        output_path = os.path.join(output_dir, f"{safe_name}.obj")

        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入元数据
            f.write(f"# Module: {module.module_name}\n")
            f.write(f"# Source Range: 0x{module.start_offset:08X}-0x{module.end_offset:08X}\n\n")

            # 写入顶点
            for v in module.vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # 写入UV
            if module.uvs:
                f.write("\n")
                for uv in module.uvs:
                    f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            # 写入面
            if module.faces:
                f.write("\n")
                for face in module.faces:
                    f.write(f"f {' '.join(f'{v}//' for v in face)}\n")

            # 写入材质引用
            if module.materials:
                f.write(f"\nmtllib materials.mtl\nusemtl {module.materials[0]}\n")

    # 生成材质文件
    with open(os.path.join(output_dir, "materials.mtl"), 'w') as f:
        f.write("newmtl 0.png\nmap_Kd 0.png\n\n")
        f.write("newmtl 1.png\nmap_Kd 1.png\n\n")
        f.write("newmtl shadow.png\nmap_Kd shadow.png\n")

if __name__ == "__main__":
    convert_to_obj('model.1s', 'output_models')