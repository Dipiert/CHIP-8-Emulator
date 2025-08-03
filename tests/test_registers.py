from registers import EightBitRegister, TwelveBitRegister

def test_eight_bit_register_constrains_values():
    assert EightBitRegister(1).value == 1
    assert EightBitRegister(258).value == 2 

def test_twelve_bit_register_constrains_values():
    assert TwelveBitRegister(3).value == 3
    assert TwelveBitRegister(4097).value == 1