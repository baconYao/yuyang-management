#!/usr/bin/env python3
# flake8: noqa: E501
"""
Generate fake data for development and testing.

This script generates:
- 35 customers: 10 TERMINATED (no cooperation), 25 ACTIVE (with cooperation)
- ACTIVE customers each have 1-3 contracts
"""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.schemas.contract import (
    BillingInterval,
    ContractStatus,
    InvoiceType,
    PaymentMethod,
)
from app.api.schemas.customer import CustomerStatus, CustomerType
from app.config import db_settings
from app.database.models.contract import Contract
from app.database.models.customer import Customer

# Chinese company names for more realistic data
COMPANY_NAMES = [
    "台北科技股份有限公司",
    "新竹電子企業",
    "台中實業有限公司",
    "高雄建設開發",
    "桃園物流服務",
    "台南食品加工",
    "基隆港務運輸",
    "新北資訊科技",
    "彰化農業合作社",
    "屏東觀光發展",
    "宜蘭文創產業",
    "花蓮石材加工",
    "台東農產運銷",
    "苗栗陶瓷工藝",
    "南投茶葉產銷",
    "雲林畜牧業",
    "嘉義木工家具",
    "澎湖海產批發",
    "金門酒業",
    "馬祖觀光飯店",
    "永和房地產",
    "板橋教育機構",
    "三重製造業",
    "中和貿易公司",
    "新店零售業",
    "樹林木材加工",
    "鶯歌陶瓷藝術",
    "三峽老街文化",
    "淡水觀光遊艇",
    "八里物流倉儲",
    "五股工業區",
    "林口新市鎮",
    "蘆洲傳統市場",
    "泰山製造業",
    "新莊科技園區",
]

# Product names
PRODUCT_NAMES = [
    "x551",
    "全錄 7 代",
    "552",
    "8710",
    "8210",
    "7740",
    "477",
    "577",
    "8600",
    "476",
    "576",
]

# Address templates
ADDRESSES = [
    "台北市信義區信義路五段7號",
    "新北市板橋區文化路一段188巷",
    "台中市西屯區台灣大道三段99號",
    "高雄市前金區中正四路211號",
    "桃園市中壢區中正路100號",
    "台南市東區中華東路三段332號",
    "新竹市東區光復路二段101號",
    "基隆市仁愛區愛一路45號",
    "嘉義市西區民族路456號",
    "屏東縣屏東市自由路123號",
]

# Contact person names
CONTACT_NAMES = [
    "王小明",
    "陳美麗",
    "林志強",
    "黃淑芬",
    "張文華",
    "李雅婷",
    "吳建國",
    "劉佳玲",
    "周大偉",
    "鄭雅文",
    "蔡明志",
    "許淑娟",
    "楊文傑",
    "謝佳蓉",
    "羅志明",
]


def generate_phone() -> str:
    """Generate a random Taiwan phone number."""
    prefixes = ["02", "03", "04", "05", "06", "07", "08", "09"]
    prefix = random.choice(prefixes)
    if prefix == "02":
        number = f"{random.randint(20000000, 29999999)}"
    elif prefix == "09":
        number = f"{random.randint(10000000, 99999999)}"
    else:
        number = f"{random.randint(1000000, 9999999)}"
    return f"{prefix}-{number}"


def generate_line_id() -> str:
    """Generate a random Line ID."""
    return f"line_{random.randint(100000, 999999)}"


def generate_invoice_number() -> str:
    """Generate a random invoice number."""
    year = random.randint(2020, 2024)
    number = random.randint(10000000, 99999999)
    return f"{year}{number:08d}"


NUM_TERMINATED = 10  # customers with no cooperation
NUM_ACTIVE = 25  # customers with cooperation


def generate_customer(index: int) -> Customer:
    """Generate a fake customer. First 10 are TERMINATED, rest are ACTIVE."""
    customer_types = list(CustomerType)
    customer_type = customer_types[index % len(customer_types)]
    status = (
        CustomerStatus.TERMINATED if index < NUM_TERMINATED else CustomerStatus.ACTIVE
    )

    company_name = COMPANY_NAMES[index % len(COMPANY_NAMES)]
    contact_name = CONTACT_NAMES[index % len(CONTACT_NAMES)]
    address = ADDRESSES[index % len(ADDRESSES)]

    return Customer(
        id=uuid4(),
        customer_name=company_name,
        invoice_title=company_name,
        invoice_number=generate_invoice_number(),
        contact_phone=generate_phone(),
        messaging_app_line=generate_line_id(),
        address=address,
        primary_contact=contact_name,
        customer_type=customer_type,
        status=status,
        created_at=datetime.now() - timedelta(days=random.randint(30, 365)),
        updated_at=datetime.now() - timedelta(days=random.randint(0, 30)),
    )


def generate_contract(customer_id: str, contract_index: int) -> Contract:
    """Generate a fake contract for a customer."""
    # Random start date within last 2 years
    start_date = datetime.now() - timedelta(
        days=random.randint(0, 730),
    )

    # Random billing interval
    billing_intervals = list(BillingInterval)
    billing_interval = random.choice(billing_intervals)
    interval_months = int(billing_interval.value)

    # End date based on billing interval (contracts typically last 1-3 years)
    contract_duration_months = random.choice([12, 18, 24, 36])
    end_date = start_date + timedelta(days=contract_duration_months * 30)

    # Status based on dates
    now = datetime.now()
    if end_date < now:
        status = random.choice([ContractStatus.ENDED, ContractStatus.TERMINATED])
    elif start_date > now:
        status = ContractStatus.PENDING
    else:
        status = random.choice([ContractStatus.ACTIVE, ContractStatus.TRIAL])

    # Monthly rent (in TWD)
    monthly_rent = random.choice([5000, 8000, 10000, 12000, 15000, 20000, 25000, 30000])

    # Payment method
    payment_method = random.choice(list(PaymentMethod))

    # Signed date (before or on start date)
    signed_date = start_date - timedelta(days=random.randint(0, 30))

    # Next billing date (if active)
    next_billing_date = None
    if status == ContractStatus.ACTIVE:
        # Calculate next billing date based on last billing
        last_billing = start_date
        while last_billing < now:
            last_billing += timedelta(days=interval_months * 30)
        next_billing_date = last_billing

    # Contract number
    year = start_date.year
    contract_number = f"CONTRACT-{year}-{contract_index:03d}"

    # Notes (optional)
    notes = None
    if random.random() < 0.3:  # 30% chance of having notes
        notes_list = [
            "客戶要求每月月初付款",
            "特殊折扣已申請",
            "需要額外維護服務",
            "合約到期前需提前通知",
            "付款方式可調整",
        ]
        notes = random.choice(notes_list)

    # Termination info (if terminated)
    terminated_at = None
    termination_reason = None
    if status == ContractStatus.TERMINATED:
        terminated_at = start_date + timedelta(
            days=random.randint(30, contract_duration_months * 30),
        )
        termination_reasons = [
            "客戶提前終止",
            "違約終止",
            "雙方協議終止",
            "其他原因",
        ]
        termination_reason = random.choice(termination_reasons)

    invoice_type = random.choice(list(InvoiceType))

    return Contract(
        id=uuid4(),
        customer_id=customer_id,
        product_name=random.choice(PRODUCT_NAMES),
        start_date=start_date,
        end_date=end_date,
        monthly_rent=monthly_rent,
        billing_interval=billing_interval,
        notes=notes,
        status=status,
        contract_number=contract_number,
        signed_date=signed_date,
        payment_method=payment_method,
        next_billing_date=next_billing_date,
        invoice_type=invoice_type,
        terminated_at=terminated_at,
        termination_reason=termination_reason,
        created_at=start_date - timedelta(days=random.randint(1, 7)),
        updated_at=datetime.now() - timedelta(days=random.randint(0, 7)),
    )


async def generate_fake_data():
    """Generate and insert fake data into the database."""
    # Create database engine
    engine = create_async_engine(
        url=db_settings.POSTGRES_URL,
        echo=False,  # Disable SQL logging for cleaner output
    )

    # Create session
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        print("Generating fake data...")

        # Generate 35 customers: 10 TERMINATED, 25 ACTIVE
        customers = []
        for i in range(NUM_TERMINATED + NUM_ACTIVE):
            customer = generate_customer(i)
            customers.append(customer)
            session.add(customer)

        await session.commit()
        print(f"✓ Created {len(customers)} customers")

        # Generate contracts for ACTIVE customers only (indices 10-34)
        total_contracts = 0
        contract_index = 1

        print(f"  - {NUM_TERMINATED} customers without cooperation (TERMINATED)")
        print(
            f"  - {NUM_ACTIVE} customers with cooperation (ACTIVE), 1-3 contracts each"
        )

        for i in range(NUM_TERMINATED, NUM_TERMINATED + NUM_ACTIVE):
            customer = customers[i]
            num_contracts = random.randint(1, 3)
            for _ in range(num_contracts):
                contract = generate_contract(customer.id, contract_index)
                session.add(contract)
                total_contracts += 1
                contract_index += 1

        await session.commit()
        print(
            f"✓ Created {total_contracts} contracts for {NUM_ACTIVE} ACTIVE customers"
        )

        print("\n" + "=" * 50)
        print("Summary:")
        print(f"  - Total customers: {len(customers)}")
        print(f"  - TERMINATED (no cooperation): {NUM_TERMINATED}")
        print(f"  - ACTIVE (with cooperation): {NUM_ACTIVE}")
        print(f"  - Total contracts: {total_contracts}")
        print("=" * 50)
        print("\n✓ Fake data generation completed!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(generate_fake_data())
