from app.api.schemas.customer import CustomerRead, CustomerType, CustomerWrite


class CustomerService:
    """Customer service for managing customer data in memory"""

    def __init__(self):
        """Initialize the service with in-memory storage"""
        self._customers: dict[int, CustomerRead] = {}
        self._next_id: int = 1
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample customer data"""
        sample_customers = [
            CustomerWrite(
                customer_name="遠雄建設股份有限公司",
                invoice_title="遠雄建設股份有限公司",
                invoice_number="INV-2024-001",
                contact_phone="02-2345-6789",
                messaging_app="Line",
                address="台北市信義區信義路五段7號",
                primary_contact="王小明",
                customer_type=CustomerType.REAL_ESTATE,
            ),
            CustomerWrite(
                customer_name="台北市立第一小學",
                invoice_title="台北市立第一小學",
                invoice_number="INV-2024-002",
                contact_phone="02-1234-5678",
                messaging_app="Line",
                address="台北市大安區和平東路一段123號",
                primary_contact="李美華",
                customer_type=CustomerType.EDUCATION,
            ),
            CustomerWrite(
                customer_name="科技新創有限公司",
                invoice_title="科技新創有限公司",
                invoice_number="INV-2024-003",
                contact_phone="02-9876-5432",
                messaging_app="Line",
                address="新北市板橋區文化路一段188巷7號",
                primary_contact="張三",
                customer_type=CustomerType.COMPANY,
            ),
        ]

        for customer in sample_customers:
            self.create(customer)

    def get_by_id(self, customer_id: int) -> CustomerRead | None:
        """
        Get a customer by ID

        Args:
            customer_id: The ID of the customer to retrieve

        Returns:
            CustomerRead if found, None otherwise
        """
        return self._customers.get(customer_id)

    def get_all(self) -> list[CustomerRead]:
        """
        Get all customers

        Returns:
            List of all customers
        """
        return list(self._customers.values())

    def create(self, customer: CustomerWrite) -> CustomerRead:
        """
        Create a new customer

        Args:
            customer: Customer data to create

        Returns:
            Created customer with assigned ID
        """
        customer_id = self._next_id
        self._next_id += 1

        customer_read = CustomerRead(
            id=customer_id,
            customer_name=customer.customer_name,
            invoice_title=customer.invoice_title,
            invoice_number=customer.invoice_number,
            contact_phone=customer.contact_phone,
            messaging_app=customer.messaging_app,
            address=customer.address,
            primary_contact=customer.primary_contact,
            customer_type=customer.customer_type,
        )

        self._customers[customer_id] = customer_read
        return customer_read
