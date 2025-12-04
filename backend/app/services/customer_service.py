from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas.customer import CustomerRead, CustomerWrite
from app.database.models.customer import Customer


class CustomerService:
    """Customer service for managing customer data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

    async def get_by_id(self, customer_id: UUID) -> CustomerRead | None:
        """
        Get a customer by ID

        Args:
            customer_id: The ID of the customer to retrieve

        Returns:
            CustomerRead if found, None otherwise
        """
        # Validate customer_id before querying database
        if customer_id is None:
            return None

        statement = select(Customer).where(Customer.id == customer_id)
        result = await self._session.execute(statement)
        db_customer = result.scalar_one_or_none()
        if db_customer is None:
            return None
        return CustomerRead.model_validate(db_customer)

    async def get_all(self) -> list[CustomerRead]:
        """
        Get all customers

        Returns:
            List of all customers
        """
        statement = select(Customer)
        result = await self._session.execute(statement)
        db_customers = result.scalars().all()
        return [CustomerRead.model_validate(customer) for customer in db_customers]  # noqa: E501

    async def create(self, customer: CustomerWrite) -> CustomerRead | None:
        """
        Create a new customer

        Args:
            customer: Customer data to create

        Returns:
            Created customer with assigned ID
        """
        if customer is None:
            return None

        # Create database model instance
        db_customer = Customer(
            customer_name=customer.customer_name,
            invoice_title=customer.invoice_title,
            invoice_number=customer.invoice_number,
            contact_phone=customer.contact_phone,
            messaging_app_line=customer.messaging_app_line,
            address=customer.address,
            primary_contact=customer.primary_contact,
            customer_type=customer.customer_type,
        )

        # Add to session and commit
        self._session.add(db_customer)
        await self._session.commit()
        await self._session.refresh(db_customer)

        # Convert to read schema
        return CustomerRead.model_validate(db_customer)
