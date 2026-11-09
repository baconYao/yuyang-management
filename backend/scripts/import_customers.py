"""Import cleaned customer CSV into the customer table.

Usage (from backend/):
    python -m scripts.import_customers path/to/customers.csv          # dry run
    python -m scripts.import_customers path/to/customers.csv --apply  # write to DB

Columns used: 客戶名稱, 發票抬頭, 統編, 聯絡電話, 縣市, 地址, 主要聯絡人, 客戶類型.
Required DB fields are never NULL: blanks get the placeholders below.
Customers whose name already exists are skipped (re-running is safe).
"""

import argparse
import asyncio
import csv
import sys
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.api.schemas.customer import CustomerType
from app.database.models.customer import Customer
from app.database.session import engine

PLACEHOLDER_PHONE = "99999999"
PLACEHOLDER_ADDRESS = "台灣"
PLACEHOLDER_CONTACT = "負責人"

TYPE_MAP = {
    "房仲": CustomerType.REAL_ESTATE,
    "文教": CustomerType.EDUCATION,
    "國小附幼": CustomerType.ELEMENTARY_ATTACHED_KINDERGARTEN,
    "公司": CustomerType.COMPANY,
    "保險": CustomerType.INSURANCE,
    "其他": CustomerType.OTHER,
}


def parse_row(row: dict[str, str]) -> Customer:
    """Map one CSV row to a Customer; raise ValueError on unusable rows."""
    name = row["客戶名稱"].strip()
    city = row["縣市"].strip()
    if not name or not city:
        raise ValueError(f"missing name or city: {row}")
    if row["客戶類型"].strip() not in TYPE_MAP:
        raise ValueError(f"unknown customer type: {row['客戶類型']!r} ({name})")
    return Customer(
        customer_name=name,
        invoice_title=row["發票抬頭"].strip() or None,
        # In this system invoice_number holds the 統一編號 (UI label + bill PDF)
        invoice_number=row["統編"].strip() or None,
        contact_phone=row["聯絡電話"].strip() or PLACEHOLDER_PHONE,
        city=city,
        address=row["地址"].strip() or PLACEHOLDER_ADDRESS,
        primary_contact=row["主要聯絡人"].strip() or PLACEHOLDER_CONTACT,
        customer_type=TYPE_MAP[row["客戶類型"].strip()],
    )


def load(path: str) -> list[Customer]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [parse_row(r) for r in csv.DictReader(f)]


async def main(path: str, apply: bool) -> None:
    customers = load(path)
    print(f"{len(customers)} rows parsed")
    print("by type:", dict(Counter(c.customer_type.value for c in customers)))
    print(
        "placeholders: phone",
        sum(c.contact_phone == PLACEHOLDER_PHONE for c in customers),
        "| address",
        sum(c.address == PLACEHOLDER_ADDRESS for c in customers),
    )
    if not apply:
        print("dry run, nothing written (use --apply)")
        return
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        existing = set(
            (await session.execute(select(Customer.customer_name))).scalars()
        )
        new = [c for c in customers if c.customer_name not in existing]
        session.add_all(new)
        await session.commit()
    print(f"inserted {len(new)}, skipped {len(customers) - len(new)} existing names")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    try:
        asyncio.run(main(a.csv, a.apply))
    except ValueError as e:
        sys.exit(str(e))
