from enum import Enum, auto


class Distro(Enum):
    win64 = auto()
    win64_manual = auto()
    osx = auto()
    linux64 = auto()


class Build(Enum):
    alpha = auto()
    demo = auto()
    headless = auto()
