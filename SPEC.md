# Custom Columnar File Format Specification (CCF)

## Overview
CCF is a binary columnar file format designed for efficient analytical workloads.
Data is stored column-wise, enabling compression and selective column reads
without scanning the entire file.

## File Extension
`.ccf`

## Binary Layout

[HEADER][COLUMN_BLOCK_0][COLUMN_BLOCK_1]...[COLUMN_BLOCK_N]

---

## Header Structure

| Offset | Size | Type | Description |
|------|------|------|-------------|
| 0 | 4 bytes | char[4] | Magic number: "CCFV" |
| 4 | 4 bytes | uint32 | Number of rows (little-endian) |
| 8 | 4 bytes | uint32 | Number of columns (little-endian) |
| 12 | Variable | bytes | Column metadata entries |

---

## Column Metadata (per column)

| Size | Type | Description |
|------|------|-------------|
| 1 byte | uint8 | Column name length (N) |
| N bytes | char[N] | Column name (UTF-8) |
| 1 byte | uint8 | Data type (0=int32, 1=float64, 2=string) |
| 8 bytes | uint64 | File offset to column data block |
| 4 bytes | uint32 | Compressed block size |
| 4 bytes | uint32 | Uncompressed block size |

---

## Supported Data Types

### INT32 (type = 0)
- 32-bit signed integer
- Little-endian
- Fixed width (4 bytes per row)

### FLOAT64 (type = 1)
- 64-bit IEEE 754 floating-point
- Little-endian
- Fixed width (8 bytes per row)

### STRING (type = 2)
- Variable-length UTF-8 encoded strings
- Stored using offset array + concatenated data

---

## String Encoding Layout

String columns are stored in two parts:

1. **Offset Array**
   - uint32 array of length = number of rows
   - Each value represents cumulative byte offset of string end

2. **String Data Block**
   - All strings concatenated back-to-back
   - No separators

### Example

Strings: `["hi", "world"]`  
Offsets: `[2, 7]`  # cumulative byte positions  
Data: `"hiworld"`

---

## Compression

- Each column block is compressed **independently**
- Compression algorithm: **zlib (level 6)**
- Enables selective decompression of requested columns only
- Header stores both compressed and uncompressed sizes

---

## Endianness

All multi-byte numeric values use **little-endian** byte order.

---

## Magic Number

The first 4 bytes of the file are the ASCII string:

CCFV
Used to validate file format correctness.
