# Pydantic v2 Quick Reference Guide

## For New Models

When creating new Pydantic models, use this modern syntax:

### Basic Model
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str
    age: int
```

### Model with ORM Support
```python
from pydantic import BaseModel, ConfigDict

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str
```

### Model with JSON Schema Example
```python
from pydantic import BaseModel, Field, ConfigDict

class CreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "age": 30
            }
        }
    )
    
    name: str = Field(..., description="User's full name")
    age: int = Field(..., ge=0, le=150, description="User's age")
```

### Generic Model
```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
```

## Common ConfigDict Options

```python
from pydantic import ConfigDict

model_config = ConfigDict(
    # For ORM models (SQLAlchemy, etc.)
    from_attributes=True,
    
    # For JSON schema examples
    json_schema_extra={"example": {...}},
    
    # Other useful options
    str_strip_whitespace=True,
    validate_assignment=True,
    use_enum_values=True,
    arbitrary_types_allowed=True,
)
```

## Migration Cheat Sheet

| Pydantic v1 | Pydantic v2 |
|-------------|-------------|
| `orm_mode = True` | `from_attributes=True` |
| `schema_extra = {...}` | `json_schema_extra={...}` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `GenericModel` | `BaseModel` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `.parse_raw()` | `.model_validate_json()` |

## ❌ Don't Use (Deprecated)

```python
# ❌ OLD - Will show deprecation warnings
class MyModel(BaseModel):
    field: str
    
    class Config:
        orm_mode = True
        schema_extra = {"example": {...}}
```

## ✅ Use Instead

```python
# ✅ NEW - Pydantic v2 style
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {...}}
    )
    
    field: str
```

## Tips

1. **Always import ConfigDict**: `from pydantic import ConfigDict`
2. **Place model_config first**: Before field definitions for readability
3. **Use descriptive Field definitions**: Helps with API documentation
4. **Test ORM conversion**: Ensure `from_attributes=True` works with your models

## Resources

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [ConfigDict Documentation](https://docs.pydantic.dev/latest/api/config/)
- [Field Documentation](https://docs.pydantic.dev/latest/api/fields/)
