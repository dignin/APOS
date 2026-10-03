"""Validate a complete CSV before changing the catalog."""
import csv
import io

MAX_CSV_BYTES = 512 * 1024
MAX_CSV_ROWS = 500


def parse_catalog(data, parse_price):
    if len(data) > MAX_CSV_BYTES:
        raise ValueError("CSV file must be no larger than 512 KiB.")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Save the CSV as UTF-8.") from None
    first_line = content.splitlines()[0] if content.splitlines() else ""
    delimiter = ";" if ";" in first_line else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter, strict=True)
    required = {"name", "price_eur", "price_usd"}
    optional = {"in_stock", "active"}
    headers = reader.fieldnames or []
    if not required.issubset(headers) or len(headers) != len(set(headers)) or set(headers) - required - optional:
        raise ValueError("CSV headers must be name,price_eur,price_usd with optional in_stock and active.")
    rows, seen = [], set()
    for row in reader:
        if len(rows) >= MAX_CSV_ROWS:
            raise ValueError("CSV may contain at most 500 products.")
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV row {reader.line_num}: incorrect number of columns.")
        name = row["name"].strip()
        if not name or len(name) > 120:
            raise ValueError(f"CSV row {reader.line_num}: name must contain 1–120 characters.")
        if name.casefold() in seen:
            raise ValueError(f"CSV row {reader.line_num}: duplicate product name.")
        seen.add(name.casefold())
        def boolean(field):
            value = row.get(field, "true").strip().lower()
            if value in ("1", "true", "yes", "ja"):
                return 1
            if value in ("0", "false", "no", "nein"):
                return 0
            raise ValueError(f"CSV row {reader.line_num}: {field} must be true or false.")
        try:
            eur = parse_price(row["price_eur"].strip().replace(",", "."))
            usd = parse_price(row["price_usd"].strip().replace(",", "."))
        except ValueError as error:
            raise ValueError(f"CSV row {reader.line_num}: {error}") from None
        rows.append({"name":name,"cents":eur,"usd_cents":usd,"in_stock":boolean("in_stock"),"active":boolean("active")})
    if not rows:
        raise ValueError("CSV contains no products.")
    return rows
