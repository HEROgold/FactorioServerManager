from enum import Enum, auto


class Distro(Enum):
    WIN64 = auto()
    WIN64_MANUAL = auto()
    OSX = auto()
    LINUX64 = auto()


class Build(Enum):
    ALPHA = auto()
    DEMO = auto()
    HEADLESS = auto()
