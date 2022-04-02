from enum import Enum


class PromptDrinking(Enum):
    UNSET = 0
    # i take it serious
    NONE = 1
    # i'm not a narc, live your life
    SOME = 2
    # drinking & golfing, in that order
    LOTS = 3


class PromptMethod(Enum):
    UNSET = 0
    # push or carry
    WALK = 1
    # motor cart
    RIDE = 2


class PromptCondition(Enum):
    UNSET = 0
    # long as there isn't lightning
    ANYTHING = 1
    # don't mind a slight wind or drizzle
    AVERAGE = 2
    # flawless or near it
    PERFECT = 3


class PromptGimme(Enum):
    UNSET = 0
    # pace of play, guys
    POLITE = 1
    # in the leather
    FRIENDLY = 2
    # no such thing
    NEVER = 3


class PaceDuration(Enum):
    UNSET = 0
    # grip it and rip it
    FAST = 1
    # nice little setup
    AVERAGE = 2
    # this is a whole day
    SLOW = 3
