import datetime as _dt
import pathlib as _pl
import secrets as _sec
import typing as _tp

import pydantic as _pyd
import sqlalchemy as _sqla
import sqlmodel as _sqlm

_T = _tp.TypeVar("_T")
_TDeco = _tp.TypeVar("_TDeco", bound=_sqla.TypeDecorator)


UNDEFINED = object()


def create_type_decorator(
    clazz: _tp.Type[_T], length: int = 2048, key: str | None = None
) -> _tp.Type[_sqla.TypeDecorator]:
    class TypeDecorator(_sqla.TypeDecorator):
        impl = _sqla.String(length)
        python_type = clazz

        def process_bind_param(self, value, dialect) -> str:
            return str(value)

        def process_result_value(self, value, dialect) -> _T:
            if key:
                return clazz(key=value)  # type: ignore[call-arg]

            return clazz(value)  # type: ignore[call-arg]

        def process_literal_param(self, value, dialect) -> str:
            return str(value)

    return TypeDecorator


def create_typed_field(
    clazz: _tp.Type[_T], *, length: int = 2048, key: str | None = None
) -> _tp.Any:
    decorator = create_type_decorator(clazz, length, key)
    return _sqlm.Field(sa_type=decorator)


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


def id_default_factory() -> str:
    return _sec.token_hex(nbytes=5)


def _create_id_field(**kwargs: _tp.Any) -> _tp.Any:
    extra_kwargs = dict(max_length=16, unique=True)

    overridden_keys = [k for k in kwargs if k in extra_kwargs]
    if overridden_keys:
        formatted_overridden_keys = ", ".join(overridden_keys)
        raise ValueError(
            f"You mustn't specify the following keys as they're overridden internally: {formatted_overridden_keys}."
        )

    return _sqlm.Field(**kwargs, **extra_kwargs)  # type: ignore[call-overload]


def create_id_field(
    default: _tp.Any = UNDEFINED,
    default_factory: _tp.Callable[[], _tp.Any] | None = None,
    foreign_key: str | None = None,
    primary_key: bool = False,
) -> _tp.Any:
    if default is not UNDEFINED and default_factory is not None:
        raise ValueError("Mustn't specify both default value and default factory.")

    nullable = default is UNDEFINED and default_factory is None

    kwargs = dict(
        default_factory=default_factory,
        foreign_key=foreign_key,
        primary_key=primary_key,
        nullable=nullable,
    )

    # SQLModels `UNDEFINED` isn't really part of its API making the `default` case a bit more complicated than the
    # `default_factory` case.
    if default is not UNDEFINED:
        return _create_id_field(default=default, **kwargs)

    return _create_id_field(**kwargs)


ID_FIELD = create_id_field(default_factory=id_default_factory, primary_key=True)

UTC_NOW_FIELD = _sqlm.Field(default_factory=utc_now)


def is_timezone_aware_in_past(datetime: _dt.datetime) -> bool:
    if datetime.tzinfo is None:
        return False

    return datetime <= utc_now()


AwarePastDatetime = _tp.Annotated[
    _dt.datetime, _pyd.AfterValidator(is_timezone_aware_in_past)
]

HTTP_URL_FIELD = create_typed_field(_pyd.HttpUrl, key="url")

PURE_WINDOWS_PATH_FIELD = create_typed_field(_pl.PureWindowsPath)
