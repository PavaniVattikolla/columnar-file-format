import struct
import zlib
import csv


class CCFWriter:
    """Writes CSV data to custom columnar format"""
    
    MAGIC = b'CCFV'
    TYPE_INT32 = 0
    TYPE_FLOAT64 = 1
    TYPE_STRING = 2
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.columns = []
        self.column_types = []
        self.data = []
        
    def infer_type(self, value):
        """Infer data type from string value"""
        if not value or value.strip() == '':
            return self.TYPE_STRING
        
        try:
            int(value)
            return self.TYPE_INT32
        except ValueError:
            pass
        
        try:
            float(value)
            return self.TYPE_FLOAT64
        except ValueError:
            pass
        
        return self.TYPE_STRING
    
    def write_from_csv(self, csv_path):
        """Read CSV and write to CCF format"""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) < 2:
            raise ValueError("CSV must have header and at least one data row")
        
        self.columns = rows[0]
        data_rows = rows[1:]
        num_rows = len(data_rows)
        num_cols = len(self.columns)
        
        # Infer types from first data row
        self.column_types = [self.infer_type(data_rows[0][i]) for i in range(num_cols)]
        
        # Organize data by columns
        self.data = [[] for _ in range(num_cols)]
        for row in data_rows:
            for col_idx in range(num_cols):
                value = row[col_idx] if col_idx < len(row) else ''
                self.data[col_idx].append(value)
        
        self._write_file(num_rows, num_cols)
    
    def _write_file(self, num_rows, num_cols):
        """Write binary CCF file"""
        with open(self.output_path, 'wb') as f:
            # Compress all columns first
            column_blocks = []
            for col_idx in range(num_cols):
                compressed = self._compress_column(col_idx, num_rows)
                column_blocks.append(compressed)
            
            # Calculate header size
            header_size = 12  # magic + rows + cols
            for col_idx in range(num_cols):
                col_name = self.columns[col_idx].encode('utf-8')
                header_size += 1 + len(col_name) + 1 + 8 + 4 + 4
            
            # Calculate offsets
            offsets = []
            current_offset = header_size
            for block in column_blocks:
                offsets.append(current_offset)
                current_offset += len(block)
            
            # Write header
            f.write(self.MAGIC)
            f.write(struct.pack('<I', num_rows))
            f.write(struct.pack('<I', num_cols))
            
            # Write column metadata
            for col_idx in range(num_cols):
                col_name = self.columns[col_idx].encode('utf-8')
                f.write(struct.pack('<B', len(col_name)))
                f.write(col_name)
                f.write(struct.pack('<B', self.column_types[col_idx]))
                f.write(struct.pack('<Q', offsets[col_idx]))
                
                compressed_data = column_blocks[col_idx]
                uncompressed_size = self._get_uncompressed_size(col_idx, num_rows)
                f.write(struct.pack('<I', len(compressed_data)))
                f.write(struct.pack('<I', uncompressed_size))
            
            # Write column data blocks
            for block in column_blocks:
                f.write(block)
    
    def _compress_column(self, col_idx, num_rows):
        """Compress column data"""
        col_type = self.column_types[col_idx]
        col_data = self.data[col_idx]
        
        if col_type == self.TYPE_INT32:
            binary = b''.join(struct.pack('<i', int(v) if v else 0) for v in col_data)
        elif col_type == self.TYPE_FLOAT64:
            binary = b''.join(struct.pack('<d', float(v) if v else 0.0) for v in col_data)
        else:  # STRING
            binary = self._encode_strings(col_data)
        
        return zlib.compress(binary, level=6)
    
    def _encode_strings(self, strings):
        """Encode variable-length strings"""
        offsets = []
        current_offset = 0
        for s in strings:
            current_offset += len(s.encode('utf-8'))
            offsets.append(current_offset)
        
        offset_block = b''.join(struct.pack('<I', off) for off in offsets)
        data_block = b''.join(s.encode('utf-8') for s in strings)
        return offset_block + data_block
    
    def _get_uncompressed_size(self, col_idx, num_rows):
        """Calculate uncompressed size"""
        col_type = self.column_types[col_idx]
        col_data = self.data[col_idx]
        
        if col_type == self.TYPE_INT32:
            return num_rows * 4
        elif col_type == self.TYPE_FLOAT64:
            return num_rows * 8
        else:  # STRING
            offset_size = num_rows * 4
            data_size = sum(len(s.encode('utf-8')) for s in col_data)
            return offset_size + data_size


# Example usage:
# writer = CCFWriter("output.ccf")
# writer.write_from_csv("data/sample.csv")
