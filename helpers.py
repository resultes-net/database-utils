import datetime as _dt
import secrets as _sec
import typing as _tp

import sqlalchemy as _sqla
import sqlmodel as _sqlm

_T = _tp.TypeVar("_T")
_TDeco = _tp.TypeVar("_TDeco", bound=_sqla.TypeDecorator)


def create_type_decorator(clazz: _tp.Type[_T], length: int = 2048, key: str | None = None) -> _tp.Type[
    _sqla.TypeDecorator]:
    class TypeDecorator(_sqla.TypeDecorator):
        impl = _sqla.String(length)
        python_type = clazz

        def process_bind_param(self, value, dialect) -> str:
            return str(value)

        def process_result_value(self, value, dialect) -> _T:
            if key:
                return clazz(key=value)

            return clazz(value)

        def process_literal_param(self, value, dialect) -> str:
            return str(value)

    return TypeDecorator


def create_typed_field(clazz: _tp.Type[_T], length: int = 2048, key: str | None = None) -> _sqlm.Field:
    decorator = create_type_decorator(clazz, length, key)
    return _sqlm.Field(sa_type=decorator)


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


ID_FIELD = _sqlm.Field(default=None, primary_key=True)


def persistent_id_factory() -> str:
    return _sec.token_hex(nbytes=5)


PERSISTENT_ID_FIELD = _sqlm.Field(default_factory=persistent_id_factory, max_length=16, unique=True, nullable=False)

UTC_NOW_FIELD = _sqlm.Field(default_factory=utc_now)
