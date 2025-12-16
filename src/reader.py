import struct
import zlib
import csv


class CCFReader:
    """Reads custom columnar format files"""
    
    MAGIC = b'CCFV'
    TYPE_INT32 = 0
    TYPE_FLOAT64 = 1
    TYPE_STRING = 2
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.num_rows = 0
        self.num_cols = 0
        self.columns = []
        self.column_types = []
        self.column_offsets = []
        self.compressed_sizes = []
        self.uncompressed_sizes = []
        
    def read_metadata(self):
        """Read file header and metadata"""
        with open(self.file_path, 'rb') as f:
            magic = f.read(4)
            if magic != self.MAGIC:
                raise ValueError(f"Invalid file format. Expected {self.MAGIC}, got {magic}")
            
            self.num_rows = struct.unpack('<I', f.read(4))[0]
            self.num_cols = struct.unpack('<I', f.read(4))[0]
            
            for _ in range(self.num_cols):
                name_len = struct.unpack('<B', f.read(1))[0]
                col_name = f.read(name_len).decode('utf-8')
                col_type = struct.unpack('<B', f.read(1))[0]
                offset = struct.unpack('<Q', f.read(8))[0]
                compressed_size = struct.unpack('<I', f.read(4))[0]
                uncompressed_size = struct.unpack('<I', f.read(4))[0]
                
                self.columns.append(col_name)
                self.column_types.append(col_type)
                self.column_offsets.append(offset)
                self.compressed_sizes.append(compressed_size)
                self.uncompressed_sizes.append(uncompressed_size)
    
    def read_columns(self, column_names=None):
        """Read specific columns or all columns"""
        self.read_metadata()
        
        if column_names is None:
            col_indices = list(range(self.num_cols))
        else:
            col_indices = [self.columns.index(name) for name in column_names]
        
        result = {self.columns[i]: [] for i in col_indices}
        
        with open(self.file_path, 'rb') as f:
            for col_idx in col_indices:
                f.seek(self.column_offsets[col_idx])
                compressed_data = f.read(self.compressed_sizes[col_idx])
                uncompressed_data = zlib.decompress(compressed_data)
                
                col_type = self.column_types[col_idx]
                if col_type == self.TYPE_INT32:
                    result[self.columns[col_idx]] = list(struct.unpack(f'<{self.num_rows}i', uncompressed_data))
                elif col_type == self.TYPE_FLOAT64:
                    result[self.columns[col_idx]] = list(struct.unpack(f'<{self.num_rows}d', uncompressed_data))
                else:  # STRING
                    result[self.columns[col_idx]] = self._decode_strings(uncompressed_data, self.num_rows)
        
        return result
    
    def _decode_strings(self, data, num_rows):
        """Decode variable-length string column"""
        offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(num_rows)]
        strings = []
        start = 0
        for end in offsets:
            strings.append(data[4*num_rows+start:4*num_rows+end].decode('utf-8'))
            start = end
        return strings
    
    def read_all(self):
        """Read all columns"""
        return self.read_columns()
