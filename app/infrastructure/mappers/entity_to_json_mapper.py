from typing import Type, TypeVar, List, Union
import json

TEntity = TypeVar("TEntity")
TSchema = TypeVar("TSchema")


class EntityJsonMapper:
    @staticmethod
    def to_json(entity: Union[TEntity, List[TEntity]], schema_cls: Type[TSchema]) -> str:
        if isinstance(entity, list):
            data = [EntityJsonMapper._to_dict(e, schema_cls) for e in entity]
        else:
            data = EntityJsonMapper._to_dict(entity, schema_cls)
        return json.dumps(data)

    @staticmethod
    def from_json(json_str: str, schema_cls: Type[TSchema], as_list: bool = False) -> Union[TSchema, List[TSchema]]:
        data = json.loads(json_str)
        if as_list:
            return [schema_cls(**item) for item in data]
        return schema_cls(**data)

    @staticmethod
    def _to_dict(entity: TEntity, schema_cls: Type[TSchema]) -> dict:
        return {field: getattr(entity, field) for field in schema_cls.model_fields if hasattr(entity, field)}
