import pathlib as _pl
import secrets as _sec
import typing as _tp

import pydantic as _pyd
import resultes_pydantic_models.common as _pcom
import sqlalchemy as _sqla
import sqlalchemy.types as _sqlt
import sqlmodel as _sqlm

UNDEFINED = object()


def id_default_factory() -> str:
    return _sec.token_hex(nbytes=5)


def _create_id_field(**kwargs: _tp.Any) -> _tp.Any:
    extra_kwargs = dict(max_length=16)

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

UTC_NOW_FIELD = _sqlm.Field(default_factory=_pcom.utc_now)


class NullableHttpUrlTypeDecorator(_sqlt.TypeDecorator):
    impl = _sqla.String(1024)
    python_type = _pyd.HttpUrl

    def process_bind_param(
        self, value: _tp.Any | None, dialect: _sqla.Dialect
    ) -> str | None:
        if value is None:
            return None

        return str(value)

    def process_result_value(
        self, value: _tp.Any | None, dialect: _sqla.Dialect
    ) -> _pyd.HttpUrl | None:
        if value is None:
            return None

        return _pyd.HttpUrl(url=value)


HTTP_URL_FIELD = _sqlm.Field(
    sa_type=NullableHttpUrlTypeDecorator,
    nullable=True,
)


class PureWindowsPathTypeDecorator(_sqla.TypeDecorator):
    impl = _sqla.String(1024)
    python_type = _pl.PureWindowsPath

    def process_bind_param(self, value, dialect) -> str:
        return str(value)

    def process_result_value(self, value, dialect) -> _pl.PureWindowsPath:
        return _pl.PureWindowsPath(value)


PURE_WINDOWS_PATH_FIELD = _sqlm.Field(
    sa_type=PureWindowsPathTypeDecorator,  # sa_column_kwargs=dict(postgresql_length=1024)
)
