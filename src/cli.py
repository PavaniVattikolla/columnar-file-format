import argparse
from src.writer import CCFWriter
from src.reader import CCFReader
import csv

def csv_to_ccf(args):
    writer = CCFWriter(args.output)
    writer.write_from_csv(args.input)
    print(f"CSV '{args.input}' successfully written to CCF '{args.output}'.")

def ccf_to_csv(args):
    reader = CCFReader(args.input)
    data = reader.read_all()
    columns = list(data.keys())
    rows = list(zip(*[data[col] for col in columns]))
    
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    print(f"CCF '{args.input}' successfully converted to CSV '{args.output}'.")

def read_columns(args):
    reader = CCFReader(args.input)
    data = reader.read_columns(args.columns.split(','))
    print(data)

def main():
    parser = argparse.ArgumentParser(description="Custom Columnar File Format CLI")
    subparsers = parser.add_subparsers()

    # CSV → CCF
    parser_csv_to_ccf = subparsers.add_parser('csv-to-ccf')
    parser_csv_to_ccf.add_argument('input', help='Input CSV file')
    parser_csv_to_ccf.add_argument('output', help='Output CCF file')
    parser_csv_to_ccf.set_defaults(func=csv_to_ccf)

    # CCF → CSV
    parser_ccf_to_csv = subparsers.add_parser('ccf-to-csv')
    parser_ccf_to_csv.add_argument('input', help='Input CCF file')
    parser_ccf_to_csv.add_argument('output', help='Output CSV file')
    parser_ccf_to_csv.set_defaults(func=ccf_to_csv)

    # Read specific columns
    parser_read = subparsers.add_parser('read')
    parser_read.add_argument('input', help='Input CCF file')
    parser_read.add_argument('--columns', required=True, help='Comma-separated column names to read')
    parser_read.set_defaults(func=read_columns)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
