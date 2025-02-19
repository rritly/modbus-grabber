from typing import Literal, Final, Any, Set
from datetime import datetime
from struct import pack, unpack
from enum import Enum
from logging import Logger, getLogger
from app.actions_exceptions import ReadActionType, ControllerException


class Parser:
    _MODBUS_TYPES: Final = {
        'BOOL': (1, False),
        'SIGN_16': (1, 0),
        'UNSIGN_16': (1, 0),
        'SIGN_32': (2, 0),
        'UNSIGN_32': (2, 0),
        'SIGN_64': (4, 0),
        'UNSIGN_64': (4, 0),
        'FLOAT_BE': (2, 0.0),  # float big endian
        'FLOAT_LE': (2, 0.0),  # float little endian
        'FLOAT_BEBS': (2, 0.0),  # float big endian byte swap
        'FLOAT_LEBS': (2, 0.0),  # float little endian byte swap
    }

    def __init__(self, logger: Logger | None = None) -> None:
        self.input_bits: list = []
        self.input_regs: list = []
        self.coils: list = []
        self.holding_regs: list = []
        self.len_input_bits: int = 0
        self.len_coils_bits: int = 0
        self.len_input_words: int = 0
        self.len_output_words: int = 0
        self.parse_inputs: list = []
        self.parse_outputs: list = []
        self.outputs_keys: Set[str] = set()
        self.config: dict = {}
        self.read_input_dict: dict = {}
        self.read_output_dict: dict = {}
        self.logger = logger if logger is not None else getLogger(__name__)

    def parese_config(self, config: Any) -> None:
        self.config = dict(config)
        try:
            self.input_bits = self.config["CONTROLLER"]["INPUT_DATA"]["input_bits"].splitlines()
            self.input_regs = self.config["CONTROLLER"]["INPUT_DATA"]["input_registers"].splitlines()
            self.coils = self.config["CONTROLLER"]["OUTPUT_DATA"]["coils"].splitlines()
            self.holding_regs = self.config["CONTROLLER"]["OUTPUT_DATA"]["holding_registers"].splitlines()
        except Exception as error:
            message = f"Failed extracting config, date:{datetime.now().isoformat()}, reason: {error}"
            self.logger.error(message)
            raise Exception(message)
        self.len_input_bits = len(self.input_bits)
        self.len_coils_bits = len(self.coils)
        try:
            # Раскладывание конфига с регистрами чтения на [(addr, key, data_type),  ]
            self.parse_inputs = [
                (int(parts[0]), parts[1], parts[2], Parser._MODBUS_TYPES[parts[2]][0])
                for item in self.input_bits + self.input_regs
                for parts in [item.split(" ")]
            ]
            # Создание словаря 'read'. Подсчет длины input registers.
            for addr, key, data_type, len_w in self.parse_inputs:
                self.read_input_dict[key] = Parser._MODBUS_TYPES[data_type][1]
                if data_type != "BOOL":
                    self.len_input_words += len_w
        except Exception as error:
            message = f"Failed parsing 'self.parse_inputs', date:{datetime.now().isoformat()}, reason: {error}"
            self.logger.error(message)
            raise Exception(message)
        try:
            # Раскладывание конфига с регистрами записи на [(addr, key, data_type),  ]
            self.parse_outputs = [
                (int(parts[0]), parts[1], parts[2], Parser._MODBUS_TYPES[parts[2]][0])
                for item in self.coils + self.holding_regs
                for parts in [item.split(" ")]
            ]
            self.outputs_keys = {item[1] for item in self.parse_outputs}
            # Создание словаря 'write'. Подсчет длины input registers.
            for addr, key, data_type, len_w in self.parse_outputs:
                self.read_output_dict[key] = Parser._MODBUS_TYPES[data_type][1]
                if data_type != "BOOL":
                    self.len_output_words += len_w
        except Exception as error:
            message = f"Failed parsing 'self.parse_outputs', date:{datetime.now().isoformat()}, reason: {error}"
            self.logger.error(message)
            raise Exception(message)

    @staticmethod
    def int16_to_modbus(value: int, type_interpret: str) -> list | None:
        if type_interpret == "SIGN_16":
            if 0 <= value <= 32767:
                return [value]
            elif -32768 <= value <= -1:
                return [value + 65536]
            else:
                return None
        elif type_interpret == "UNSIGN_16":
            if 0 <= value <= 65535:
                return [value]
            else:
                return None
        else:
            return None

    @staticmethod
    def int32_to_modbus(value: int, type_interpret: str) -> list | None:
        wordorder = "big"
        byteorder = "big"
        format_d = ">i"
        limit_min = 0
        limit_max = 4294967295
        if type_interpret == "UNSIGN_32":
            format_d = ">I"
            limit_min = 0
            limit_max = 4294967295
        elif type_interpret == "SIGN_32":
            limit_min = -2147483648
            limit_max = 2147483647
            format_d = ">i"
        if limit_min <= value <= limit_max:
            packed = pack(format_d, value)
            if byteorder == "little":
                packed = packed[::-1]
            high, low = unpack(">HH", packed)
            if wordorder == "little":
                return [low, high]
            else:
                return [high, low]
        else:
            return None

    @staticmethod
    def int64_to_modbus(value: int, type_interpret: str) -> list | None:
        wordorder = "big"
        byteorder = "big"
        format_d = ">q"
        limit_min = 0
        limit_max = 18446744073709551615
        if type_interpret == "UNSIGN_64":
            format_d = ">Q"
            limit_min = 0
            limit_max = 18446744073709551615
        elif type_interpret == "SIGN_64":
            format_d = ">q"
            limit_min = -9223372036854775808
            limit_max = 9223372036854775807
        if limit_min <= value <= limit_max:
            packed = pack(format_d, value)
            if byteorder == "little":
                packed = packed[::-1]
            high0, high1, low0, low1 = unpack(">HHHH", packed)
            if wordorder == "little":
                return [low0, low1, high0, high1]
            else:
                return [high0, high1, low0, low1]
        else:
            return None

    @staticmethod
    def float_to_modbus(value, type_interpret: str) -> list | None:
        wordorder = "big"
        byteorder = "big"
        if -3.4028235e38 <= value <= 3.4028235e38:
            if type_interpret == "FLOAT_BE":
                wordorder = "big"
                byteorder = "big"
            elif type_interpret == "FLOAT_LE":
                wordorder = "big"
                byteorder = "little"
            elif type_interpret == "FLOAT_BEBS":
                wordorder = "little"
                byteorder = "little"
            elif type_interpret == "FLOAT_LEBS":
                wordorder = "little"
                byteorder = "big"
            packed = pack(">f", value)
            if byteorder == "little":
                packed = packed[::-1]
            high, low = unpack(">HH", packed)
            if wordorder == "little":
                return [low, high]
            else:
                return [high, low]
        else:
            return None

    def parse_data_from_modbus(
        self,
        in_bits: list | None = None,
        in_registers: list | None = None,
        out_bits: list | None = None,
        out_registers: list | None = None,
        mode: Enum = ReadActionType.READ_ALL,
    ) -> dict[
        Literal["READ_INPUT_DATA", "READ_OUTPUT_DATA"], dict[str, bool | int | float] | None
    ]:
        """
        Получает необработанные данные из modbus и преобразует в словарь

        :param in_bits: дискретные входы modbus
        :param in_registers: аналоговые входы modbus
        :param out_bits: катушки modbus
        :param out_registers: регистры хранения modbus
        :param mode: Режим чтения. Всё сразу, или только регистры хранения, или только регистры входов
        :return: {"READ_INPUT_DATA": {имя регистра: значение}, "READ_OUTPUT_DATA": {} }
        """
        data_bits: list = []
        data_reg: list = []
        parsed_config: list = []
        dict_writing: dict = {}
        returned_data = None

        if mode == ReadActionType.READ_ALL:
            returned_data = self.parse_data_from_modbus(
                out_bits=out_bits,
                out_registers=out_registers,
                mode=ReadActionType.READ_HOLDINGS,
            )
            mode = ReadActionType.READ_INPUTS
        if mode == ReadActionType.READ_HOLDINGS:
            parsed_config = self.parse_outputs
            if isinstance(out_bits, list):
                data_bits = out_bits
            if isinstance(out_registers, list):
                data_reg = out_registers
            dict_writing = self.read_output_dict
        if mode == ReadActionType.READ_INPUTS:
            parsed_config = self.parse_inputs
            if isinstance(in_bits, list):
                data_bits = in_bits
            if isinstance(in_registers, list):
                data_reg = in_registers
            dict_writing = self.read_input_dict

        for addr, key, data_type, _ in parsed_config:
            match data_type:
                case "BOOL":
                    dict_writing[key] = data_bits[addr]
                case "UNSIGN_16":
                    dict_writing[key] = data_reg[addr]
                case "SIGN_16":
                    if data_reg[addr] < 32768:
                        dict_writing[key] = data_reg[addr]
                    else:
                        dict_writing[key] = data_reg[addr] - 65536
                case "UNSIGN_32":
                    dict_writing[key] = unpack(
                        ">I",
                        pack(
                            ">HH",
                            data_reg[addr],
                            data_reg[addr + 1],
                        ),
                    )[0]
                case "SIGN_32":
                    dict_writing[key] = unpack(
                        ">i",
                        pack(
                            ">HH",
                            data_reg[addr],
                            data_reg[addr + 1],
                        ),
                    )[0]
                case "UNSIGN_64":
                    dict_writing[key] = unpack(
                        ">Q",
                        pack(
                            ">HHHH",
                            data_reg[addr],
                            data_reg[addr + 1],
                            data_reg[addr + 2],
                            data_reg[addr + 3],
                        ),
                    )[0]
                case "SIGN_64":
                    dict_writing[key] = unpack(
                        ">q",
                        pack(
                            ">HHHH",
                            data_reg[addr],
                            data_reg[addr + 1],
                            data_reg[addr + 2],
                            data_reg[addr + 3],
                        ),
                    )[0]
                case "FLOAT_BE":
                    dict_writing[key] = unpack(
                        ">f",
                        pack(
                            ">HH",
                            data_reg[addr],
                            data_reg[addr + 1],
                        ),
                    )[0]
                case "FLOAT_LE":  # float little endian
                    dict_writing[key] = unpack(
                        ">f",
                        pack(
                            "<HH",
                            data_reg[addr + 1],
                            data_reg[addr],
                        ),
                    )[0]
                case "FLOAT_BEBS":  # float big endian byte swap
                    dict_writing[key] = unpack(
                        ">f",
                        pack(
                            "<HH",
                            data_reg[addr],
                            data_reg[addr + 1],
                        ),
                    )[0]
                case "FLOAT_LEBS":  # float little endian byte swap
                    dict_writing[key] = unpack(
                        ">f",
                        pack(
                            ">HH",
                            data_reg[addr + 1],
                            data_reg[addr],
                        ),
                    )[0]
        if returned_data is None:
            if mode == ReadActionType.READ_INPUTS:
                return {
                    "READ_INPUT_DATA": dict_writing,
                    "READ_OUTPUT_DATA": None,
                }
            elif mode == ReadActionType.READ_HOLDINGS:
                return {
                    "READ_INPUT_DATA": None,
                    "READ_OUTPUT_DATA": dict_writing,
                }
            else:
                raise ValueError(f"Unsupported mode: {mode}")
        else:
            returned_data["READ_INPUT_DATA"] = dict_writing
            return returned_data

    def parse_data_to_modbus(
        self, data: dict
    ) -> dict[Literal["coils", "registers"], dict[int, list] | None]:
        """
        Кодирует значения согласно стандарту modbus
        Сортирует данные в последовательные пакеты для мин. кол-ва записей

        :param data: Словарь для записи {Имя регистра: Значение, ..}
        :return: {'coils': {Стартовый адрес: [True, ..], ..}, 'registers': {Стартовый адрес: [32000, ..], ..}}
        """
        bool_data: list = []
        bool_data_sorted: list[list] = [[]]
        num_data: list = []
        num_data_sorted: list[list] = [[]]
        # Проверка ключей
        # Заполнение массива отсутствующих ключей
        missing_keys = [key for key in data if key not in self.outputs_keys]
        if missing_keys:
            message = f"Keys {missing_keys} don't exist! {datetime.now().isoformat()}"
            self.logger.error(message)
            raise ControllerException(message)
        try:
            # Разделение катушек и регистров на отдельные массивы
            for addr, key, data_type, len_data in self.parse_outputs:
                if key in data:
                    if data_type == "BOOL":
                        bool_data.append((addr, key, data[key]))
                    else:
                        incorrect_data = data[key]
                        match data_type:
                            case "SIGN_16" | "UNSIGN_16":
                                data[key] = Parser.int16_to_modbus(data[key], data_type)
                            case "SIGN_32" | "UNSIGN_32":
                                data[key] = Parser.int32_to_modbus(data[key], data_type)
                            case "SIGN_64" | "UNSIGN_64":
                                data[key] = Parser.int64_to_modbus(data[key], data_type)
                            case "FLOAT_BE" | "FLOAT_LE" | "FLOAT_BEBS" | "FLOAT_LEBS":
                                data[key] = Parser.float_to_modbus(data[key], data_type)
                        if data[key] is None:
                            raise ControllerException(
                                f"Value {incorrect_data}, key's '{key}'({data_type}) is out of range!"
                            )
                        num_data.append((addr, key, data[key], data_type, len_data))
        except Exception as error:
            message = f"Failed encoding to modbus data format, date:{datetime.now().isoformat()}, reason: {error}"
            self.logger.error(message)
            raise Exception(message)
        try:
            # Формирование массива [[(адрес, имя, значение), ], [.., ..,]]
            # Для катушек
            if bool_data:
                count_pack_coil = 0
                for i, _ in enumerate(bool_data):
                    if i + 1 == len(bool_data):
                        bool_data_sorted[count_pack_coil].append(bool_data[i])
                        break
                    if bool_data[i][0] == bool_data[i + 1][0] - 1:
                        bool_data_sorted[count_pack_coil].append(bool_data[i])
                    else:
                        bool_data_sorted[count_pack_coil].append(bool_data[i])
                        count_pack_coil += 1
                        bool_data_sorted.append([])
                # serialized_coil -- {стартовый адрес: массив данных}
                serialized_coil = {
                    group[0][0]: [item[2] for item in group]
                    for group in bool_data_sorted
                }
            else:
                serialized_coil = None
        except Exception as error:
            message = (
                f"Failed to sort the coils packets for writing to modbus, date:{datetime.now().isoformat()},"
                f" reason: {error}"
            )
            self.logger.error(message)
            raise Exception(message)
        try:
            # Формирование массива [[(адрес, имя, значение, тип, длина), ], [.., ..,]]
            # Для регистров
            if num_data:
                count_pack_reg = 0
                serialized_reg = {}
                for i, _ in enumerate(num_data):
                    if i + 1 == len(num_data):
                        num_data_sorted[count_pack_reg].append(num_data[i])
                        break
                    if num_data[i][0] + (num_data[i][4] - 1) == num_data[i + 1][0] - 1:
                        num_data_sorted[count_pack_reg].append(num_data[i])
                    else:
                        num_data_sorted[count_pack_reg].append(num_data[i])
                        count_pack_reg += 1
                        num_data_sorted.append([])
                for serial_elem in num_data_sorted:
                    # serialized_reg -- {стартовый адрес: массив данных}
                    serialized_reg[serial_elem[0][0]] = [
                        item for sublist in serial_elem for item in sublist[2]
                    ]
            else:
                serialized_reg = None
        except Exception as error:
            message = (
                f"Failed to sort the holding registers packets for writing to modbus!"
                f" date:{datetime.now().isoformat()}, reason: {error}"
            )
            self.logger.error(message)
            raise Exception(message)
        return {"coils": serialized_coil, "registers": serialized_reg}
