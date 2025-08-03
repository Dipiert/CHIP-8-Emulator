import binascii
import logging
from registers import v_registers, I
from pprint import pprint as pp
import pygame

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROGRAM_COUNTER = "0x200"
OPCODES_BYTES_OFFSET = "2"
RETURN_TO = None
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
SCREEN = [[hex(0)] * SCREEN_WIDTH] * SCREEN_HEIGHT
#pp(SCREEN)

def parse_src_code(path: str) -> dict[str, str]:
    parsed = {}
    # Historically, the CHIP-8 interpreter itself occupies the first 512 bytes of the memory space on these machines.
    # For this reason, most programs written for the original system begin at memory location 512 (0x200)
    # and do not access any of the memory below the location 512 (0x200)
    memory_address = "0x200"
    with open(path, "rb") as f:
        while True:
            chunk = f.read(2)

            if not chunk:
                break

            parsed[memory_address] = binascii.hexlify(chunk).decode('ascii')
            memory_address = hex(int(memory_address, 16) + int(OPCODES_BYTES_OFFSET, 16))

    return parsed


def _set_vx_to_nn(opcode: str) -> None:
    register = opcode[1]
    value = opcode[2:]
    value = int(value, 16)
    v_registers[register] = hex(value)
    logger.debug("Set register V%s to %s", register, value)


def _call_subroutine_at_nnn(opcode: str, code: dict) -> None:
    address = f"0x{opcode[1:]}"
    logger.debug("Calling subroutine @ %s", address)
    global PROGRAM_COUNTER
    PROGRAM_COUNTER = address


def _set_vx_to_vy(opcode):
    vx = opcode[1]
    vy = opcode[2]
    logger.debug("Setting V%s to the value of V%s", vx, vy)
    v_registers[vx] = v_registers[vy]


def move_pc_fwd(n_offsets=1):
    global PROGRAM_COUNTER
    PROGRAM_COUNTER = hex(int(PROGRAM_COUNTER, 16) + int(OPCODES_BYTES_OFFSET, 16) * n_offsets)
    logger.debug("Moving PROGRAM_COUNTER to %s", PROGRAM_COUNTER)

def _set_I_to_the_address_nnn(opcode):
    global I
    value = opcode[1:]
    logger.debug("Setting I to address 0x%s", value)
    I = f"0x{opcode[1:]}"


def _skip_next_if_vx_ne_nn(opcode):
    v = opcode[1]
    nn = opcode[2:]
    vx = v_registers[v]
    if int(vx, 16) == int(nn, 16):
        return 1
    else:
        logger.debug("Skipping next instruction as V%s (%s) != to %s", v, int(vx, 16), nn)
        return 2

def _skip_next_if_vx_e_nn(opcode):
    if PROGRAM_COUNTER == '0x28e':
        print()
    v = opcode[1]
    nn = opcode[2:]
    vx = v_registers[v]
    if int(vx, 16) == int(nn, 16):
        logger.debug("Skipping next instruction as V%s (%s) == to %s", v, int(vx, 16), nn)
        return 2
    else:
        logger.debug(
            "V%s (%s) != NN (%s), then executing next instruction",
            v, vx, nn
        )
        return 1


def _add_vx_to_i(opcode):
    global I
    v = opcode[1]
    vx = v_registers[v]
    logger.debug("Adding V%s (%s) to I", v, int(vx, 16))
    I = hex(int(I, 16) + int(opcode[1], 16))
    logger.debug("I now is: %s", I)


def _add_nn_to_vx(opcode):
    v = opcode[1]
    vx = v_registers[v]
    nn = opcode[-2:]
    logger.debug("Adding NN (%s) to V%s", int(nn, 16), v)
    v_registers[v] = hex(int(vx, 16) + int(nn, 16))


def _jump_to_address_nnn(opcode):
    global PROGRAM_COUNTER
    address = f"0x{opcode[1:]}"
    logger.debug("Jumping to address %s", address)
    PROGRAM_COUNTER = address


def _read_n_bytes_of_data(n, code):
    n = int(n)
    result = []
    if n == int(OPCODES_BYTES_OFFSET):
        return code[I]
    else:
        i = I
        remaining = n // 2
        while remaining:
            result.append(code[i][:2])
            result.append(code[i][2:])
            remaining -= 1
            i = hex(int(i, 16) + int(OPCODES_BYTES_OFFSET, 16))
        return result


def _draw_sprite(opcode, code):
    """
    The two registers passed to this instruction determine the x and y location of the sprite
    on the screen. If the sprite is to be visible on the screen,
    the VX register must contain a value between 00 and 3F,
    and the VY register must contain a value between 00 and 1F.
    When this instruction is processed by the interpreter, N bytes of data are read
    from memory starting from the address stored in register I.
    These bytes then represent the sprite data that will be used to draw the sprite
    on the screen. Therefore, the value of the I register determines which sprite is drawn,
    and should always point to the memory address where the sprite data for the
    desired graphic is stored. The corresponding graphic on the screen will be
    eight pixels wide and N pixels high.
    """
    x_coord = int(opcode[1])
    y_coord = int(opcode[2])
    n = int(opcode[3])
    width = 8 # Sprites are always 8 pixels wide

    logger.debug("Reading %s bytes of data starting at %s", n, I)
    data = _read_n_bytes_of_data(n, code)
    logger.debug("Read: %s", data)

    # Make the drawing fit in the screen
    x_coord = x_coord % SCREEN_WIDTH
    y_coord = y_coord % SCREEN_HEIGHT

    pygame.init()
    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    window.fill(0)

    to_draw = []
    for i in range(n):
        screen_data = str(SCREEN[x_coord][y_coord + i])
        I_data = str(data[i])
        to_draw.append(int(screen_data, 16) ^ int(I_data, 16))
    
    logger.debug("To draw: %s", to_draw)

    for i, pixel in enumerate(to_draw):
        if pixel:
            for w in range(width):
                window.set_at((x_coord+w, y_coord+i), (255, 255, 255))
                SCREEN[x_coord][y_coord] = 'ff'
              
    pygame.display.flip()


def exec(code: dict[str: str]) -> None:
    global PROGRAM_COUNTER, RETURN_TO
    opcode = code[PROGRAM_COUNTER]
    while True:
        #print(f"Return to: {RETURN_TO}")
        if opcode == "00ee": #20 421
            if not RETURN_TO:
                break
            else:
                logger.debug("Returning from sub-routine. Moving PROGRAM_COUNTER to %s", RETURN_TO)
                PROGRAM_COUNTER = RETURN_TO
        elif opcode == "00e0":
                logger.debug("Clear screen")
                move_pc_fwd()
                opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "1":
            _jump_to_address_nnn(opcode)
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "2":
            RETURN_TO = hex(int(PROGRAM_COUNTER, 16) + int(OPCODES_BYTES_OFFSET, 16))
            logger.debug("Storing subroutine return address as %s", RETURN_TO)
            _call_subroutine_at_nnn(opcode, code)
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "3":
            n_offsets = _skip_next_if_vx_e_nn(opcode)
            move_pc_fwd(n_offsets)
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "4":
            n_offsets = _skip_next_if_vx_ne_nn(opcode)
            move_pc_fwd(n_offsets)
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "6":
            _set_vx_to_nn(opcode)
            move_pc_fwd()
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "7":
            _add_nn_to_vx(opcode)
            move_pc_fwd()
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "8":
            if opcode[3] == "0":
                _set_vx_to_vy(opcode)
                move_pc_fwd()
                opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "a":
            _set_I_to_the_address_nnn(opcode)
            move_pc_fwd()
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "d":
            _draw_sprite(opcode, code)
            move_pc_fwd()
            opcode = code[PROGRAM_COUNTER]

        elif opcode[0] == "f":
            if opcode[-2:] == "1e":
                _add_vx_to_i(opcode)
                move_pc_fwd()
                opcode = code[PROGRAM_COUNTER]
    
        else:
            return


if __name__ == '__main__':
    parsed = parse_src_code("examples/cavern.ch8")
    exec(parsed)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

