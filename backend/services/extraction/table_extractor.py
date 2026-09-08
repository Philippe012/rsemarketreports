
from typing import List

TableRows = List[List[str]]


def extract_page_tables(page) -> List[TableRows]:
    tables = []
    for raw_table in page.extract_tables() or []:
        cleaned = [
            [('' if cell is None else str(cell).strip()) for cell in row]
            for row in raw_table
        ]
        tables.append(cleaned)
    return tables


def extract_all_tables(pdf) -> List[List[TableRows]]:
    return [extract_page_tables(page) for page in pdf.pages]


def flatten_table_text(table: TableRows) -> str:
    lines = []
    for row in table:
        for cell in row:
            if cell:
                lines.extend(cell.splitlines())
    return '\n'.join(lines)
