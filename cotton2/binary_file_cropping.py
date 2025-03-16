import sys


def convert_to_int(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.startswith('0x'):
        return int(value, 16)
    return int(value)


def extract_binary_section(input_file, output_file, start, end):
    try:
        start = convert_to_int(start)
        end = convert_to_int(end)
        with open(input_file, 'rb') as infile:
            infile.seek(start)
            data = infile.read(end - start)

        with open(output_file, 'wb') as outfile:
            outfile.write(data)

        print(f"成功从 {input_file} 截取 {start}-{end} 字节到 {output_file}。")
    except FileNotFoundError:
        print(f"错误: 文件 {input_file} 未找到。")
    except Exception as e:
        print(f"错误: 发生未知错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("用法: python script.py <输入文件> <输出文件> <起始字节> <结束字节>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    start = sys.argv[3]
    end = sys.argv[4]

    try:
        start = convert_to_int(start)
        end = convert_to_int(end)
        if start < 0 or end <= start:
            print("错误: 起始字节必须是非负的，且结束字节必须大于起始字节。")
            sys.exit(1)
        extract_binary_section(input_file, output_file, start, end)
    except ValueError:
        print("错误: 起始或结束字节不是有效的数字。")
