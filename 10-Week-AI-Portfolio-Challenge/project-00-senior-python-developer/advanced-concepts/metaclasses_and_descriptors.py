"""
Advanced Python: Metaclasses and Descriptors
Demonstrates senior-level understanding of Python's object model
"""

from typing import Any, Dict, Optional, Type, Union
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# =============================================================================
# METACLASSES: Classes that create classes
# =============================================================================

class SingletonMeta(type):
    """
    Metaclass that implements the Singleton pattern.
    Demonstrates metaclass usage for design patterns.
    """
    _instances: Dict[Type, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DatabaseConnection(metaclass=SingletonMeta):
    """Example singleton class using metaclass."""
    
    def __init__(self):
        self.connected = False
        logger.info("Database connection instance created")
    
    def connect(self):
        self.connected = True
        logger.info("Connected to database")


class ValidatedMeta(type):
    """
    Metaclass that adds validation to class creation.
    Demonstrates metaclass usage for framework development.
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Validate class definition
        if 'required_methods' in namespace:
            required = namespace['required_methods']
            for method in required:
                if method not in namespace:
                    raise TypeError(f"Class {name} must implement {method}")
        
        # Add automatic validation
        if hasattr(mcs, '_add_validation'):
            mcs._add_validation(namespace)
        
        return super().__new__(mcs, name, bases, namespace)
    
    @staticmethod
    def _add_validation(namespace: dict):
        """Add validation methods to the class."""
        original_init = namespace.get('__init__', lambda self: None)
        
        def validated_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._validate()
        
        namespace['__init__'] = validated_init
        
        if '_validate' not in namespace:
            namespace['_validate'] = lambda self: None


class FieldMeta(type):
    """
    Metaclass for ORM-like field collection.
    Demonstrates advanced metaclass usage for framework development.
    """
    
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        # Collect field definitions
        fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                fields[key] = value
                value.name = key
                # Remove field from namespace to avoid conflicts
                del namespace[key]
        
        # Store fields in class
        namespace['_fields'] = fields
        namespace['_field_names'] = list(fields.keys())
        
        # Add field access methods
        mcs._add_field_methods(namespace, fields)
        
        return super().__new__(mcs, name, bases, namespace)
    
    @staticmethod
    def _add_field_methods(namespace: dict, fields: Dict[str, 'Field']):
        """Add methods for field access and validation."""
        
        def __init__(self, **kwargs):
            for name, field in self._fields.items():
                value = kwargs.get(name, field.default)
                field.validate(value)
                setattr(self, f"_{name}", value)
        
        def __getattribute__(self, name: str):
            if name.startswith('_') or name in ['_fields', '_field_names']:
                return object.__getattribute__(self, name)
            
            if name in self._fields:
                return object.__getattribute__(self, f"_{name}")
            
            return object.__getattribute__(self, name)
        
        def __setattr__(self, name: str, value: Any):
            if name in self._fields:
                self._fields[name].validate(value)
                object.__setattr__(self, f"_{name}", value)
            else:
                object.__setattr__(self, name, value)
        
        namespace['__init__'] = __init__
        namespace['__getattribute__'] = __getattribute__
        namespace['__setattr__'] = __setattr__


# =============================================================================
# DESCRIPTORS: Attribute access control
# =============================================================================

class Field(ABC):
    """
    Base descriptor class for typed fields.
    Demonstrates descriptor protocol implementation.
    """
    
    def __init__(self, default: Any = None, required: bool = False):
        self.default = default
        self.required = required
        self.name: Optional[str] = None
    
    def __set_name__(self, owner: Type, name: str):
        """Called when descriptor is assigned to class attribute."""
        self.name = name
        self.private_name = f'_{name}'
    
    def __get__(self, obj: Any, objtype: Optional[Type] = None):
        """Get attribute value."""
        if obj is None:
            return self
        return getattr(obj, self.private_name, self.default)
    
    def __set__(self, obj: Any, value: Any):
        """Set attribute value with validation."""
        self.validate(value)
        setattr(obj, self.private_name, value)
    
    def __delete__(self, obj: Any):
        """Delete attribute."""
        if self.required:
            raise AttributeError(f"Cannot delete required field {self.name}")
        delattr(obj, self.private_name)
    
    @abstractmethod
    def validate(self, value: Any) -> None:
        """Validate field value."""
        pass


class StringField(Field):
    """String field with length validation."""
    
    def __init__(self, max_length: Optional[int] = None, min_length: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
    
    def validate(self, value: Any) -> None:
        if value is None and self.required:
            raise ValueError(f"Field {self.name} is required")
        
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(f"Field {self.name} must be a string")
            
            if len(value) < self.min_length:
                raise ValueError(f"Field {self.name} must be at least {self.min_length} characters")
            
            if self.max_length and len(value) > self.max_length:
                raise ValueError(f"Field {self.name} must be at most {self.max_length} characters")


class IntegerField(Field):
    """Integer field with range validation."""
    
    def __init__(self, min_value: Optional[int] = None, max_value: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> None:
        if value is None and self.required:
            raise ValueError(f"Field {self.name} is required")
        
        if value is not None:
            if not isinstance(value, int):
                raise TypeError(f"Field {self.name} must be an integer")
            
            if self.min_value is not None and value < self.min_value:
                raise ValueError(f"Field {self.name} must be at least {self.min_value}")
            
            if self.max_value is not None and value > self.max_value:
                raise ValueError(f"Field {self.name} must be at most {self.max_value}")


class EmailField(StringField):
    """Email field with format validation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def validate(self, value: Any) -> None:
        super().validate(value)
        if value is not None and '@' not in value:
            raise ValueError(f"Field {self.name} must be a valid email address")


class CachedProperty:
    """
    Descriptor that caches property values.
    Demonstrates descriptor usage for performance optimization.
    """
    
    def __init__(self, func):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
    
    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise RuntimeError(
                f"Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )
    
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        try:
            cache = instance.__dict__
        except AttributeError:
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attrname!r} property."
            )
            raise TypeError(msg) from None
        val = cache.get(self.attrname, self)
        if val is self:
            val = self.func(instance)
            try:
                cache[self.attrname] = val
            except TypeError:
                msg = (
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                    f"does not support item assignment for caching {self.attrname!r} property."
                )
                raise TypeError(msg) from None
        return val


class WeakProperty:
    """
    Descriptor that stores values using weak references.
    Demonstrates advanced descriptor patterns for memory management.
    """
    
    def __init__(self):
        import weakref
        self.data = weakref.WeakKeyDictionary()
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.data.get(instance)
    
    def __set__(self, instance, value):
        self.data[instance] = value
    
    def __delete__(self, instance):
        try:
            del self.data[instance]
        except KeyError:
            pass


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

class User(metaclass=FieldMeta):
    """
    Example model using metaclass and descriptors.
    Demonstrates ORM-like functionality.
    """
    
    name = StringField(max_length=100, required=True)
    email = EmailField(required=True)
    age = IntegerField(min_value=0, max_value=150)
    bio = StringField(max_length=500, default="")
    
    @CachedProperty
    def display_name(self) -> str:
        """Cached property that formats the display name."""
        return f"{self.name} <{self.email}>"
    
    def __repr__(self) -> str:
        return f"User(name={self.name!r}, email={self.email!r}, age={self.age})"


class APIModel(metaclass=ValidatedMeta):
    """Example class using validation metaclass."""
    
    required_methods = ['to_dict', 'from_dict']
    
    def to_dict(self) -> dict:
        return {'validated': True}
    
    def from_dict(self, data: dict):
        pass
    
    def _validate(self):
        """Custom validation logic."""
        logger.info("Model validation passed")


# =============================================================================
# DEMONSTRATION AND TESTING
# =============================================================================

def demonstrate_metaclasses():
    """Demonstrate metaclass functionality."""
    print("=== Metaclass Demonstrations ===")
    
    # Singleton pattern
    print("\n1. Singleton Pattern:")
    db1 = DatabaseConnection()
    db2 = DatabaseConnection()
    print(f"Same instance: {db1 is db2}")  # True
    
    # Field collection
    print("\n2. Field Collection:")
    user = User(name="John Doe", email="john@example.com", age=30)
    print(f"User: {user}")
    print(f"Fields: {user._field_names}")
    print(f"Display name: {user.display_name}")  # Cached
    print(f"Display name: {user.display_name}")  # From cache


def demonstrate_descriptors():
    """Demonstrate descriptor functionality."""
    print("\n=== Descriptor Demonstrations ===")
    
    # Field validation
    print("\n1. Field Validation:")
    try:
        user = User(name="", email="invalid", age=-5)
    except ValueError as e:
        print(f"Validation error: {e}")
    
    # Proper field usage
    user = User(name="Jane Smith", email="jane@example.com", age=25)
    print(f"Valid user: {user}")
    
    # Cached property
    print(f"\n2. Cached Property:")
    print(f"First access: {user.display_name}")
    print(f"Second access: {user.display_name}")  # From cache


def performance_comparison():
    """Compare performance with and without descriptors."""
    import time
    
    class SimpleUser:
        def __init__(self, name, email, age):
            self.name = name
            self.email = email
            self.age = age
    
    # Test performance
    iterations = 100000
    
    # Simple class
    start = time.time()
    for i in range(iterations):
        user = SimpleUser(f"User{i}", f"user{i}@example.com", 25)
    simple_time = time.time() - start
    
    # Descriptor class
    start = time.time()
    for i in range(iterations):
        try:
            user = User(name=f"User{i}", email=f"user{i}@example.com", age=25)
        except:
            pass  # Some might fail validation
    descriptor_time = time.time() - start
    
    print(f"\n=== Performance Comparison ===")
    print(f"Simple class: {simple_time:.4f}s")
    print(f"Descriptor class: {descriptor_time:.4f}s")
    print(f"Overhead: {(descriptor_time / simple_time - 1) * 100:.1f}%")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run demonstrations
    demonstrate_metaclasses()
    demonstrate_descriptors()
    performance_comparison()
    
    print("\n=== Summary ===")
    print("✅ Metaclasses: Control class creation and add functionality")
    print("✅ Descriptors: Control attribute access with validation")
    print("✅ Performance: Understand trade-offs of advanced features")
    print("✅ Real-world: ORM-like functionality with type safety")