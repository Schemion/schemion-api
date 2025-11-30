from datetime import datetime
from typing import Type, TypeVar, List, Union
import json
from uuid import UUID

TEntity = TypeVar("TEntity")
TSchema = TypeVar("TSchema")

def default_json_serializer(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class EntityJsonMapper:
    @staticmethod
    def to_json(entity: Union[TEntity, List[TEntity]], schema_cls: Type[TSchema]) -> str:
        if isinstance(entity, list):
            data = [EntityJsonMapper._to_dict(e, schema_cls) for e in entity]
        else:
            data = EntityJsonMapper._to_dict(entity, schema_cls)
        return json.dumps(data, default=default_json_serializer)

    @staticmethod
    def from_json(json_str_or_dict: Union[str, dict, List[dict]], schema_cls: Type[TSchema], as_list: bool = False) -> Union[TSchema, List[TSchema]]:
        if isinstance(json_str_or_dict, str):
            data = json.loads(json_str_or_dict)
        else:
            data = json_str_or_dict

        if as_list:
            return [schema_cls(**item) for item in data]
        return schema_cls(**data)

    @staticmethod
    def _to_dict(entity: TEntity, schema_cls: Type[TSchema]) -> dict:
        return {field: getattr(entity, field) for field in schema_cls.model_fields if hasattr(entity, field)}
