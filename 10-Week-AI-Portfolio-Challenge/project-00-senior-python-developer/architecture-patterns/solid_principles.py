"""
SOLID Principles Implementation in Python
Demonstrates senior-level understanding of software design principles
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# 1. SINGLE RESPONSIBILITY PRINCIPLE (SRP)
# "A class should have only one reason to change"
# =============================================================================

# ❌ BAD: Violates SRP - multiple responsibilities
class BadUserManager:
    """Anti-pattern: Class with multiple responsibilities."""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, user_data: dict):
        # Validation logic
        if not user_data.get('email') or '@' not in user_data['email']:
            raise ValueError("Invalid email")
        
        # Business logic
        user = {
            'id': len(self.users) + 1,
            'email': user_data['email'],
            'name': user_data['name']
        }
        self.users.append(user)
        
        # Persistence logic
        self._save_to_database(user)
        
        # Notification logic
        self._send_welcome_email(user['email'])
    
    def _save_to_database(self, user):
        # Database code here
        pass
    
    def _send_welcome_email(self, email):
        # Email sending code here
        pass


# ✅ GOOD: Follows SRP - single responsibility per class
@dataclass
class User:
    """Domain model with single responsibility."""
    id: Optional[int]
    email: str
    name: str
    
    def __post_init__(self):
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email format")


class UserValidator:
    """Single responsibility: User validation."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(email and '@' in email and '.' in email)
    
    @staticmethod
    def validate_name(name: str) -> bool:
        return bool(name and len(name.strip()) >= 2)
    
    def validate_user(self, user_data: dict) -> bool:
        return (
            self.validate_email(user_data.get('email', '')) and
            self.validate_name(user_data.get('name', ''))
        )


class UserRepository:
    """Single responsibility: User persistence."""
    
    def __init__(self):
        self._users: List[User] = []
        self._next_id = 1
    
    def save(self, user: User) -> User:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
        
        self._users.append(user)
        logger.info(f"User {user.id} saved to database")
        return user
    
    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._users if u.email == email), None)
    
    def find_all(self) -> List[User]:
        return self._users.copy()


class EmailService:
    """Single responsibility: Email notifications."""
    
    def send_welcome_email(self, email: str, name: str) -> bool:
        logger.info(f"Sending welcome email to {email}")
        # Email sending logic here
        return True
    
    def send_notification(self, email: str, subject: str, body: str) -> bool:
        logger.info(f"Sending notification to {email}: {subject}")
        # Email sending logic here
        return True


class UserService:
    """Single responsibility: User business logic orchestration."""
    
    def __init__(
        self,
        validator: UserValidator,
        repository: UserRepository,
        email_service: EmailService
    ):
        self._validator = validator
        self._repository = repository
        self._email_service = email_service
    
    def create_user(self, user_data: dict) -> User:
        # Validate input
        if not self._validator.validate_user(user_data):
            raise ValueError("Invalid user data")
        
        # Create user
        user = User(
            id=None,
            email=user_data['email'],
            name=user_data['name']
        )
        
        # Save user
        saved_user = self._repository.save(user)
        
        # Send welcome email
        self._email_service.send_welcome_email(saved_user.email, saved_user.name)
        
        return saved_user


# =============================================================================
# 2. OPEN/CLOSED PRINCIPLE (OCP)
# "Software entities should be open for extension, closed for modification"
# =============================================================================

# ✅ GOOD: Open for extension, closed for modification
class NotificationSender(ABC):
    """Abstract base for notification strategies."""
    
    @abstractmethod
    def send(self, recipient: str, subject: str, message: str) -> bool:
        pass


class EmailNotificationSender(NotificationSender):
    """Email notification implementation."""
    
    def send(self, recipient: str, subject: str, message: str) -> bool:
        logger.info(f"Email sent to {recipient}: {subject}")
        return True


class SMSNotificationSender(NotificationSender):
    """SMS notification implementation."""
    
    def send(self, recipient: str, subject: str, message: str) -> bool:
        logger.info(f"SMS sent to {recipient}: {message}")
        return True


class SlackNotificationSender(NotificationSender):
    """Slack notification implementation - EXTENSION without modification."""
    
    def send(self, recipient: str, subject: str, message: str) -> bool:
        logger.info(f"Slack message sent to {recipient}: {message}")
        return True


class NotificationService:
    """Service that uses notification strategies."""
    
    def __init__(self):
        self._senders: List[NotificationSender] = []
    
    def add_sender(self, sender: NotificationSender):
        self._senders.append(sender)
    
    def send_notification(self, recipient: str, subject: str, message: str):
        for sender in self._senders:
            try:
                sender.send(recipient, subject, message)
            except Exception as e:
                logger.error(f"Failed to send via {type(sender).__name__}: {e}")


# =============================================================================
# 3. LISKOV SUBSTITUTION PRINCIPLE (LSP)
# "Objects should be replaceable with instances of their subtypes"
# =============================================================================

# ❌ BAD: Violates LSP - Square changes Rectangle behavior
class BadRectangle:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> float:
        return self._width
    
    @width.setter
    def width(self, value: float):
        self._width = value
    
    @property
    def height(self) -> float:
        return self._height
    
    @height.setter
    def height(self, value: float):
        self._height = value
    
    def area(self) -> float:
        return self._width * self._height


class BadSquare(BadRectangle):
    """BAD: Violates LSP by changing behavior."""
    
    @property
    def width(self) -> float:
        return self._width
    
    @width.setter
    def width(self, value: float):
        self._width = value
        self._height = value  # ❌ Breaks LSP - unexpected side effect
    
    @property
    def height(self) -> float:
        return self._height
    
    @height.setter
    def height(self, value: float):
        self._width = value  # ❌ Breaks LSP - unexpected side effect
        self._height = value


# ✅ GOOD: Follows LSP with proper abstraction
class Shape(ABC):
    """Abstract shape that defines contract."""
    
    @abstractmethod
    def area(self) -> float:
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        pass


class Rectangle(Shape):
    """Rectangle implementation that follows LSP."""
    
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    @property
    def width(self) -> float:
        return self._width
    
    @property
    def height(self) -> float:
        return self._height
    
    def area(self) -> float:
        return self._width * self._height
    
    def perimeter(self) -> float:
        return 2 * (self._width + self._height)


class Square(Shape):
    """Square implementation that follows LSP."""
    
    def __init__(self, side: float):
        self._side = side
    
    @property
    def side(self) -> float:
        return self._side
    
    def area(self) -> float:
        return self._side * self._side
    
    def perimeter(self) -> float:
        return 4 * self._side


def calculate_total_area(shapes: List[Shape]) -> float:
    """Function that works with any Shape implementation."""
    return sum(shape.area() for shape in shapes)


# =============================================================================
# 4. INTERFACE SEGREGATION PRINCIPLE (ISP)
# "Clients should not depend on interfaces they don't use"
# =============================================================================

# ❌ BAD: Fat interface forces unnecessary dependencies
class BadWorkerInterface(ABC):
    """Fat interface that violates ISP."""
    
    @abstractmethod
    def work(self): pass
    
    @abstractmethod
    def eat(self): pass
    
    @abstractmethod
    def sleep(self): pass
    
    @abstractmethod
    def code(self): pass  # Not all workers code!


# ✅ GOOD: Segregated interfaces
class Workable(Protocol):
    """Interface for work capability."""
    def work(self) -> None: ...


class Eatable(Protocol):
    """Interface for eating capability."""
    def eat(self) -> None: ...


class Sleepable(Protocol):
    """Interface for sleeping capability."""
    def sleep(self) -> None: ...


class Codeable(Protocol):
    """Interface for coding capability."""
    def code(self) -> None: ...


class Human:
    """Human worker implementing relevant interfaces."""
    
    def work(self) -> None:
        logger.info("Human is working")
    
    def eat(self) -> None:
        logger.info("Human is eating")
    
    def sleep(self) -> None:
        logger.info("Human is sleeping")


class Developer(Human):
    """Developer with additional coding capability."""
    
    def code(self) -> None:
        logger.info("Developer is coding")


class Robot:
    """Robot worker implementing only relevant interfaces."""
    
    def work(self) -> None:
        logger.info("Robot is working")
    
    def code(self) -> None:
        logger.info("Robot is coding")
    
    # Note: Robot doesn't implement eat() or sleep() - follows ISP


class WorkManager:
    """Manager that uses segregated interfaces."""
    
    def manage_work(self, worker: Workable) -> None:
        worker.work()
    
    def manage_coding(self, coder: Codeable) -> None:
        coder.code()
    
    def manage_break(self, worker: Eatable) -> None:
        worker.eat()


# =============================================================================
# 5. DEPENDENCY INVERSION PRINCIPLE (DIP)
# "Depend on abstractions, not concretions"
# =============================================================================

# ❌ BAD: High-level module depends on low-level module
class BadMySQLDatabase:
    def save_user(self, user_data: dict) -> bool:
        logger.info("Saving to MySQL database")
        return True


class BadUserService:
    """BAD: Depends on concrete implementation."""
    
    def __init__(self):
        self._database = BadMySQLDatabase()  # ❌ Tight coupling
    
    def create_user(self, user_data: dict) -> bool:
        return self._database.save_user(user_data)


# ✅ GOOD: Depend on abstractions
class DatabaseInterface(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    def save_user(self, user: User) -> bool:
        pass
    
    @abstractmethod
    def find_user_by_email(self, email: str) -> Optional[User]:
        pass


class MySQLDatabase(DatabaseInterface):
    """MySQL implementation of database interface."""
    
    def save_user(self, user: User) -> bool:
        logger.info(f"Saving user {user.email} to MySQL")
        return True
    
    def find_user_by_email(self, email: str) -> Optional[User]:
        logger.info(f"Finding user {email} in MySQL")
        return None  # Simplified


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL implementation - easy to swap."""
    
    def save_user(self, user: User) -> bool:
        logger.info(f"Saving user {user.email} to PostgreSQL")
        return True
    
    def find_user_by_email(self, email: str) -> Optional[User]:
        logger.info(f"Finding user {email} in PostgreSQL")
        return None  # Simplified


class InMemoryDatabase(DatabaseInterface):
    """In-memory implementation for testing."""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
    
    def save_user(self, user: User) -> bool:
        self._users[user.email] = user
        logger.info(f"Saving user {user.email} to memory")
        return True
    
    def find_user_by_email(self, email: str) -> Optional[User]:
        return self._users.get(email)


class GoodUserService:
    """GOOD: Depends on abstraction."""
    
    def __init__(self, database: DatabaseInterface):
        self._database = database  # ✅ Depends on abstraction
    
    def create_user(self, user_data: dict) -> User:
        user = User(
            id=None,
            email=user_data['email'],
            name=user_data['name']
        )
        
        # Check if user exists
        existing_user = self._database.find_user_by_email(user.email)
        if existing_user:
            raise ValueError(f"User {user.email} already exists")
        
        # Save user
        self._database.save_user(user)
        return user


# =============================================================================
# DEPENDENCY INJECTION CONTAINER
# =============================================================================

class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[type, Any] = {}
        self._singletons: Dict[type, Any] = {}
    
    def register(self, interface: type, implementation: Any, singleton: bool = False):
        """Register service implementation."""
        if singleton:
            self._singletons[interface] = implementation
        else:
            self._services[interface] = implementation
    
    def resolve(self, interface: type) -> Any:
        """Resolve service dependency."""
        if interface in self._singletons:
            return self._singletons[interface]
        elif interface in self._services:
            return self._services[interface]() if callable(self._services[interface]) else self._services[interface]
        else:
            raise ValueError(f"Service {interface} not registered")


# =============================================================================
# DEMONSTRATION AND TESTING
# =============================================================================

def demonstrate_srp():
    """Demonstrate Single Responsibility Principle."""
    print("=== Single Responsibility Principle ===")
    
    # Setup components with single responsibilities
    validator = UserValidator()
    repository = UserRepository()
    email_service = EmailService()
    user_service = UserService(validator, repository, email_service)
    
    # Create user using composed services
    user_data = {'email': 'john@example.com', 'name': 'John Doe'}
    user = user_service.create_user(user_data)
    
    print(f"✅ User created: {user}")
    print(f"✅ Each class has single responsibility")


def demonstrate_ocp():
    """Demonstrate Open/Closed Principle."""
    print("\n=== Open/Closed Principle ===")
    
    # Create notification service
    notification_service = NotificationService()
    
    # Add different notification methods (extensions)
    notification_service.add_sender(EmailNotificationSender())
    notification_service.add_sender(SMSNotificationSender())
    notification_service.add_sender(SlackNotificationSender())  # New extension
    
    # Use without modifying existing code
    notification_service.send_notification(
        "user@example.com",
        "Welcome",
        "Welcome to our platform!"
    )
    
    print("✅ Extended functionality without modifying existing code")


def demonstrate_lsp():
    """Demonstrate Liskov Substitution Principle."""
    print("\n=== Liskov Substitution Principle ===")
    
    # Create different shapes
    shapes = [
        Rectangle(4, 5),
        Square(3),
        Rectangle(2, 8)
    ]
    
    # Function works with any Shape implementation
    total_area = calculate_total_area(shapes)
    print(f"✅ Total area of shapes: {total_area}")
    print("✅ All shapes are substitutable")


def demonstrate_isp():
    """Demonstrate Interface Segregation Principle."""
    print("\n=== Interface Segregation Principle ===")
    
    # Create workers with different capabilities
    human = Human()
    developer = Developer()
    robot = Robot()
    
    manager = WorkManager()
    
    # Use only relevant interfaces
    manager.manage_work(human)      # Uses Workable
    manager.manage_work(robot)      # Uses Workable
    manager.manage_coding(developer) # Uses Codeable
    manager.manage_coding(robot)    # Uses Codeable
    manager.manage_break(human)     # Uses Eatable
    # manager.manage_break(robot)   # Would fail - robot doesn't implement Eatable
    
    print("✅ Clients depend only on interfaces they use")


def demonstrate_dip():
    """Demonstrate Dependency Inversion Principle."""
    print("\n=== Dependency Inversion Principle ===")
    
    # Setup dependency injection
    container = DIContainer()
    
    # Register implementations
    container.register(DatabaseInterface, MySQLDatabase, singleton=True)
    
    # Resolve and use
    database = container.resolve(DatabaseInterface)
    user_service = GoodUserService(database)
    
    user = user_service.create_user({'email': 'jane@example.com', 'name': 'Jane Smith'})
    print(f"✅ User created with MySQL: {user}")
    
    # Easy to swap implementation
    container.register(DatabaseInterface, PostgreSQLDatabase, singleton=True)
    database = container.resolve(DatabaseInterface)
    user_service = GoodUserService(database)
    
    user = user_service.create_user({'email': 'bob@example.com', 'name': 'Bob Wilson'})
    print(f"✅ User created with PostgreSQL: {user}")
    print("✅ High-level modules independent of low-level implementations")


def demonstrate_all_principles():
    """Demonstrate all SOLID principles working together."""
    print("\n=== All SOLID Principles Together ===")
    
    # Setup dependency injection container
    container = DIContainer()
    
    # Register all dependencies
    container.register(UserValidator, UserValidator())
    container.register(DatabaseInterface, InMemoryDatabase(), singleton=True)
    container.register(EmailService, EmailService())
    
    # Create notification service with multiple senders
    notification_service = NotificationService()
    notification_service.add_sender(EmailNotificationSender())
    notification_service.add_sender(SMSNotificationSender())
    
    # Resolve dependencies
    validator = container.resolve(UserValidator)
    database = container.resolve(DatabaseInterface)
    email_service = container.resolve(EmailService)
    
    # Create user service
    user_service = GoodUserService(database)
    
    # Create user
    user = user_service.create_user({
        'email': 'solid@example.com',
        'name': 'SOLID Principles'
    })
    
    # Send notifications
    notification_service.send_notification(
        user.email,
        "SOLID Principles",
        "All principles working together!"
    )
    
    print("✅ All SOLID principles implemented successfully")
    print("✅ System is maintainable, extensible, and testable")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Demonstrate each principle
    demonstrate_srp()
    demonstrate_ocp()
    demonstrate_lsp()
    demonstrate_isp()
    demonstrate_dip()
    demonstrate_all_principles()
    
    print("\n=== SOLID Principles Summary ===")
    print("✅ SRP: Single Responsibility - One reason to change")
    print("✅ OCP: Open/Closed - Open for extension, closed for modification")
    print("✅ LSP: Liskov Substitution - Subtypes must be substitutable")
    print("✅ ISP: Interface Segregation - Depend only on used interfaces")
    print("✅ DIP: Dependency Inversion - Depend on abstractions, not concretions")