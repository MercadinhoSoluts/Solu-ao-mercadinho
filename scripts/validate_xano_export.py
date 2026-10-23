from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5


EXPORT_FILES = {
    "users": "users.json",
    "products": "produtos.json",
    "barcodes": "codigobarra.json",
    "stock": "estoque.json",
    "prices": "preco.json",
}
ROLE_MAP = {
    "operator": "operator",
    "caixa": "operator",
    "cashier": "operator",
    "operador": "operator",
    "operadora": "operator",
    "funcionario": "operator",
    "funcionário": "operator",
    "manager": "manager",
    "admin": "manager",
    "administrador": "manager",
    "administradora": "manager",
    "gerente": "manager",
    "gestor": "manager",
    "owner": "owner",
    "proprietario": "owner",
    "proprietário": "owner",
    "proprietaria": "owner",
    "dono": "owner",
}
INTEGER_PATTERN = re.compile(r"^[0-9]+$")


def _records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as export_file:
        payload = json.load(export_file)
    if isinstance(payload, dict):
        payload = payload.get("items", payload.get("records"))
    if not isinstance(payload, list) or any(
        not isinstance(record, dict) for record in payload
    ):
        raise ValueError(f"{path.name} must contain a JSON array of objects.")
    return payload


def _source_id(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return str(value)
    if isinstance(value, str) and INTEGER_PATTERN.fullmatch(value.strip()):
        parsed = value.strip()
        return parsed if int(parsed) > 0 else None
    return None


def _nonnegative_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and INTEGER_PATTERN.fullmatch(value.strip()):
        return int(value.strip())
    return None


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _fits_scale(value: Decimal, decimal_places: int) -> bool:
    try:
        precision = Decimal(1).scaleb(-decimal_places)
        return value == value.quantize(precision)
    except InvalidOperation:
        return False


def _pick(record: dict[str, Any], *fields: str) -> Any:
    for field in fields:
        if record.get(field) is not None:
            return record[field]
    return None


def _product_uuid(source_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"bipsystem:xano:produtos:{source_id}"))


def validate_export(directory: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    tables: dict[str, list[dict[str, Any]]] = {}
    for table, filename in EXPORT_FILES.items():
        path = directory / filename
        if not path.is_file():
            errors.append(f"Missing required export file: {filename}")
            tables[table] = []
            continue
        try:
            tables[table] = _records(path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            errors.append(f"Invalid {filename}: {error}")
            tables[table] = []

    valid_ids: dict[str, set[str]] = {}
    for table, records in tables.items():
        ids: set[str] = set()
        for index, record in enumerate(records, start=1):
            source_id = _source_id(record.get("id"))
            if source_id is None:
                errors.append(f"{EXPORT_FILES[table]} row {index} has an invalid id.")
            elif source_id in ids:
                errors.append(
                    f"{EXPORT_FILES[table]} contains duplicate source id {source_id}."
                )
            else:
                ids.add(source_id)
        valid_ids[table] = ids

    role_counts: Counter[str] = Counter()
    normalized_emails: set[str] = set()
    for index, record in enumerate(tables["users"], start=1):
        email = record.get("email")
        if not isinstance(email, str) or "@" not in email.strip():
            errors.append(f"users.json row {index} has no valid email for Auth.")
        else:
            normalized_email = email.strip().casefold()
            if normalized_email in normalized_emails:
                errors.append(
                    f"users.json contains duplicate normalized email at row {index}."
                )
            normalized_emails.add(normalized_email)

        raw_role = record.get("role")
        role = ROLE_MAP.get(str(raw_role or "operator").strip().casefold())
        if role is None:
            errors.append(f"users.json row {index} has an unsupported role.")
        else:
            role_counts[role] += 1
    if tables["users"]:
        warnings.append(
            "Xano passwords cannot be transferred to Supabase Auth; users need "
            "new credentials or a password-reset flow."
        )

    barcode_by_product: dict[str, str] = {}
    barcode_owners: dict[str, str] = {}
    for index, record in enumerate(tables["barcodes"], start=1):
        product_id = _source_id(record.get("produtos_id"))
        barcode_value = _pick(record, "codigo_de_barras", "codigo_de_barra")
        barcode = barcode_value.strip() if isinstance(barcode_value, str) else ""
        if product_id is None or product_id not in valid_ids["products"]:
            errors.append(
                f"codigobarra.json row {index} references a missing product."
            )
            continue
        if not barcode:
            errors.append(f"codigobarra.json row {index} has no barcode.")
            continue
        existing_barcode = barcode_by_product.get(product_id)
        if existing_barcode is not None:
            errors.append(
                f"Product {product_id} has multiple barcode rows; the target "
                "supports one barcode per product."
            )
        barcode_by_product[product_id] = barcode
        existing_owner = barcode_owners.get(barcode)
        if existing_owner is not None and existing_owner != product_id:
            errors.append(f"Barcode {barcode!r} belongs to multiple products.")
        barcode_owners[barcode] = product_id

    for index, record in enumerate(tables["products"], start=1):
        source_id = _source_id(record.get("id"))
        if source_id is None:
            continue
        name = _pick(record, "nome", "product_type")
        brand = _pick(record, "marca", "brand")
        weight = _decimal(_pick(record, "peso", "weight_grams"))
        if not isinstance(name, str) or not name.strip():
            errors.append(f"produtos.json row {index} has no product name/type.")
        if not isinstance(brand, str) or not brand.strip():
            errors.append(f"produtos.json row {index} has no brand.")
        if (
            weight is None
            or weight <= 0
            or not _fits_scale(weight, 3)
            or weight > Decimal("999999999.999")
        ):
            errors.append(
                f"produtos.json row {index} has an invalid weight; "
                "the target supports positive values with at most 3 decimals."
            )
        if source_id not in barcode_by_product:
            errors.append(
                f"Product {source_id} has no barcode; the target requires one."
            )

    stock_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for index, record in enumerate(tables["stock"], start=1):
        product_id = _source_id(record.get("produtos_id"))
        if product_id is None or product_id not in valid_ids["products"]:
            errors.append(f"estoque.json row {index} references a missing product.")
            continue
        batch = record.get("lote")
        units = _nonnegative_integer(record.get("unidades"))
        expiry_value = record.get("validade")
        try:
            expiry = date.fromisoformat(str(expiry_value))
        except (TypeError, ValueError):
            expiry = None
        if batch is None or not str(batch).strip():
            errors.append(f"estoque.json row {index} has no batch label.")
        if units is None:
            errors.append(
                f"estoque.json row {index} has invalid non-negative integer units."
            )
        if expiry is None:
            errors.append(f"estoque.json row {index} has an invalid expiry date.")
        if units is None or expiry is None or batch is None:
            continue
        key = (product_id, expiry.isoformat())
        current = stock_groups.get(key)
        if current is None:
            stock_groups[key] = {"units": int(units), "batch": str(batch)}
        else:
            current["units"] += int(units)
            if current["units"] > 2_147_483_647:
                errors.append(
                    f"Combined stock units exceed the PostgreSQL integer limit "
                    f"for product {product_id} and expiry {expiry.isoformat()}."
                )
            if current["batch"] != str(batch):
                warnings.append(
                    f"Product {product_id} has multiple batch labels for expiry "
                    f"{expiry.isoformat()}; the first label is retained when "
                    "matching the application's existing grouping behavior."
                )
    if stock_groups:
        warnings.append(
            "Xano stock exports contain balances, not movement history; import "
            "can preserve opening balances but cannot reconstruct past movements."
        )

    price_count = 0
    for index, record in enumerate(tables["prices"], start=1):
        product_id = _source_id(record.get("produtos_id"))
        if product_id is None or product_id not in valid_ids["products"]:
            errors.append(f"preco.json row {index} references a missing product.")
            continue
        price = _decimal(record.get("preco_unitario"))
        if (
            price is None
            or price <= 0
            or not _fits_scale(price, 2)
            or price * 100 > 9_223_372_036_854_775_807
        ):
            errors.append(
                f"preco.json row {index} has an invalid price; "
                "the target stores positive values in whole cents."
            )
            continue
        price_count += 1
        created_at = record.get("created_at")
        if created_at is not None:
            try:
                datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"preco.json row {index} has an invalid created_at.")

    product_id_map = {
        source_id: _product_uuid(source_id)
        for source_id in sorted(valid_ids["products"], key=int)
    }
    if tables["products"] and not tables["prices"]:
        warnings.append("No Xano price records were found in the export.")

    return {
        "ready_for_manual_import": not errors,
        "counts": {
            "users": len(tables["users"]),
            "products": len(tables["products"]),
            "barcode_rows": len(tables["barcodes"]),
            "stock_rows": len(tables["stock"]),
            "stock_groups_after_merge": len(stock_groups),
            "price_rows": price_count,
        },
        "role_counts": dict(sorted(role_counts.items())),
        "product_id_map": product_id_map,
        "warnings": sorted(set(warnings)),
        "errors": errors,
        "database_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Xano JSON exports without connecting to Supabase."
    )
    parser.add_argument(
        "export_directory",
        type=Path,
        help="Directory containing users.json, produtos.json, codigobarra.json, "
        "estoque.json, and preco.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the non-sensitive validation manifest.",
    )
    args = parser.parse_args()

    report = validate_export(args.export_directory)
    encoded_report = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded_report, encoding="utf-8")
    else:
        print(encoded_report, end="")
    return 0 if report["ready_for_manual_import"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
