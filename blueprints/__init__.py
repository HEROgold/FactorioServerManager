# noqa: D104
# Use a hack that allows for dynamic bp registration while also creating __all__

from .dashboard import bp as dashboard
from .login import bp as login


# fmt: off
all_blueprints = [
    login,
    dashboard
]

__all__ = [
    str(i.name)
    for i in all_blueprints
] # type: ignore[ReportUnsupportedDunderAll]
# fmt: on
