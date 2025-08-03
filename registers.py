from abc import ABC

class Register(ABC):
    def __init__(self, initial_value=0):
        self._value = self._constrain(initial_value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = self._constrain(new_value)


class EightBitRegister(Register):

    def _constrain(self, val):
        """ Constrain to 8 bits """
        return val & 0xFF

class TwelveBitRegister(Register):

    def _constrain(self, val):
        """ Constrain to 12 bits """
        return val & 0b111111111111

v_registers = {
    "0": EightBitRegister(),
    "1": EightBitRegister(),
    "2": EightBitRegister(),
    "3": EightBitRegister(),
    "4": EightBitRegister(),
    "5": EightBitRegister(),
    "6": EightBitRegister(),
    "7": EightBitRegister(),
    "8": EightBitRegister(),
    "9": EightBitRegister(),
    "A": EightBitRegister(),
    "B": EightBitRegister(),
    "C": EightBitRegister(),
    "D": EightBitRegister(),
    "E": EightBitRegister(),
    "F": EightBitRegister(),
}

I = TwelveBitRegister()