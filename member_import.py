"""Import member profiles only, never credentials or privileged roles."""
import csv
import io
from catalog_import import MAX_CSV_BYTES, MAX_CSV_ROWS


def parse_members(data):
    if len(data) > MAX_CSV_BYTES:
        raise ValueError("CSV file must be no larger than 512 KiB.")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Save the CSV as UTF-8.") from None
    first = content.splitlines()[0] if content.splitlines() else ""
    reader = csv.DictReader(io.StringIO(content), delimiter=";" if ";" in first else ",", strict=True)
    headers = reader.fieldnames or []
    if not {'name','code'}.issubset(headers) or len(headers) != len(set(headers)) or set(headers) - {'name','code','active'}:
        raise ValueError("Member CSV headers must be name,code with optional active.")
    rows, seen = [], set()
    for row in reader:
        if len(rows) >= MAX_CSV_ROWS:
            raise ValueError("CSV may contain at most 500 members.")
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV row {reader.line_num}: incorrect number of columns.")
        name, code = row['name'].strip(), row['code'].strip()
        if not name or not code or len(name) > 120 or len(code) > 120:
            raise ValueError(f"CSV row {reader.line_num}: name and code must contain 1–120 characters.")
        if code.casefold() in seen:
            raise ValueError(f"CSV row {reader.line_num}: duplicate member code.")
        seen.add(code.casefold())
        value = row.get('active','true').strip().lower()
        if value not in ('true','1','yes','ja','false','0','no','nein'):
            raise ValueError(f"CSV row {reader.line_num}: active must be true or false.")
        rows.append({'name':name,'code':code,'active':int(value in ('true','1','yes','ja'))})
    if not rows:
        raise ValueError("CSV contains no members.")
    return rows
