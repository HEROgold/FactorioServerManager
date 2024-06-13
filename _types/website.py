from os import PathLike
from typing import Self

from flask import Flask
from flask_login import LoginManager

from _types.database import User
from config import SECRET_KEY


class Website(Flask):
    def __init__(  # noqa: PLR0913
        self,  # noqa: ANN101
        import_name: str,
        *,
        static_url_path: str | None = None,
        static_folder: str | PathLike[str] | None = "static",
        static_host: str | None = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: str | PathLike[str] | None = "templates",
        instance_path: str | None = None,
        instance_relative_config: bool = False,
        root_path: str | None = None,
    ) -> None:
        super().__init__(
            import_name=import_name,
            static_url_path=static_url_path,
            static_folder=static_folder,
            static_host=static_host,
            host_matching=host_matching,
            subdomain_matching=subdomain_matching,
            template_folder=template_folder,
            instance_path=instance_path,
            instance_relative_config=instance_relative_config,
            root_path=root_path,
        )
        self.login_manager = LoginManager(self)
        self.login_manager.user_loader(self._user_loader)
        self.login_manager.login_view = "login.login" # type: ignore[reportAttributeAccessIssue]

        self.config.from_pyfile("config.py")
        self.config["SECRET_KEY"] = SECRET_KEY


    def _user_loader(self: Self, user_id: int) -> User | None:
        if user := User.get_by_user_id(user_id):
            return user
        return None
