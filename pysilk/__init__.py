import ctypes
import os

dll_path = os.path.join(os.path.dirname(__file__), "pysilk.dll")
pysilk = ctypes.CDLL(dll_path)
# int Silk2Mp3FromFile(char* inpath, char* outpath, int sr)
pysilk.Silk2Mp3FromFile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
pysilk.Silk2Mp3FromFile.restype = ctypes.c_int
#  int Silk2Mp3FromBuffer(uint8_t* silkData, size_t silkSize, const char* mp3path, int sr);\
pysilk.Silk2Mp3FromBuffer.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_int]
pysilk.Silk2Mp3FromBuffer.restype = ctypes.c_int

def silk_file_to_mp3(input_path: str, output_path: str, sample_rate: int) -> int:
    inpath = input_path.encode('utf-8')
    outpath = output_path.encode('utf-8')
    return pysilk.Silk2Mp3FromFile(inpath, outpath, sample_rate)

def silk_bytes_to_mp3(input_bytes: bytes, output_path: str, sample_rate: int) -> int:
    silk_data = ctypes.create_string_buffer(input_bytes)
    silk_size = len(input_bytes)
    outpath = output_path.encode('utf-8')
    return pysilk.Silk2Mp3FromBuffer(silk_data, silk_size, outpath, sample_rate)


# Example usage
if __name__ == "__main__":
    input_file = "150674070315722125.silk"
    output_file = input_file.replace(".silk", ".mp3")
    sample_rate = 24000  # 
    silk_file_to_mp3(input_file, output_file, sample_rate)