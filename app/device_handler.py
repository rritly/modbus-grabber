from datetime import datetime
from enum import Enum
from logging import Logger, getLogger
from typing import Literal
from app.make_modbus import Modbus
from app.parser import Parser
from app.actions_exceptions import ReadActionType


class ControllerHandler:
    def __init__(
        self,
        config: dict,
        mode_read: Enum = ReadActionType.READ_ALL,
        logger: Logger | None = None,
    ) -> None:
        self.config = dict(config)
        self.host = self.config["CONTROLLER"]["HOST"]
        self.port = self.config["CONTROLLER"]["PORT"]
        self.device = Modbus(self.host, self.port,)
        self.parser = Parser()
        self.parser.parese_config(self.config)
        self.mode_read = mode_read
        self.connected = None
        self.logger = logger if logger is not None else getLogger(__name__)

    def connect(self) -> None:
        try:
            self.connected = self.device.client.connect()
            if not self.connected:
                raise ConnectionError("Connection refused")
        except Exception as error:
            message = f"Failed connected {self.host}:{self.port}, date:{datetime.now().isoformat()}, reason: {error}"
            self.logger.error(message)
            self.device.client.close()
            raise ConnectionError(message)

    def close_connect(self) -> None:
        try:
            self.device.client.close()
        finally:
            self.connected = None

    def receive(self,) -> dict[
        Literal["READ_INPUT_DATA", "READ_OUTPUT_DATA"], dict[str, bool | int | float] | None,
    ]:
        input_bits_data = None
        input_regs_data = None
        coils_bits_data = None
        holdings_regs_data = None

        if not self.connected:
            self.connect()
        # Для discrete_inputs и input registers
        if (self.mode_read == ReadActionType.READ_ALL) | (self.mode_read == ReadActionType.READ_INPUTS):
            # discrete_inputs
            input_bits_data = self.device.input_bits(0, self.parser.len_input_bits)
            if not input_bits_data:
                message = (
                    f"Empty modbus data (input_bits) from {self.host}:{self.port},"
                    f" date:{datetime.now().isoformat()}"
                )
                self.logger.error(message)
                raise ConnectionError(message)
            # input registers
            input_regs_data = self.device.input_registers_read(0, self.parser.len_input_words)
            if not input_regs_data:
                message = (
                    f"Empty modbus data (input_registers) from {self.host}:{self.port},"
                    f" date:{datetime.now().isoformat()}"
                )
                self.logger.error(message)
                raise ConnectionError(message)
        # Для coils и holding registers
        if (self.mode_read == ReadActionType.READ_ALL) | (self.mode_read == ReadActionType.READ_HOLDINGS):
            # coils
            coils_bits_data = self.device.coils_read(0, self.parser.len_coils_bits)
            if not coils_bits_data:
                message = f"Empty modbus data (coils) from {self.host}:{self.port}, date:{datetime.now().isoformat()}"
                self.logger.error(message)
                raise ConnectionError(message)
            # holding registers
            holdings_regs_data = self.device.holding_registers_read(0, self.parser.len_output_words)
            if not holdings_regs_data:
                message = (
                    f"Empty modbus data (holding_registers) from {self.host}:{self.port},"
                    f" date:{datetime.now().isoformat()}"
                )
                self.logger.error(message)
                raise ConnectionError(message)
        # Парсинг принятых данных и получение словаря
        received_dict = self.parser.parse_data_from_modbus(
            input_bits_data,
            input_regs_data,
            coils_bits_data,
            holdings_regs_data,
            self.mode_read,
        )
        return received_dict

    def transmit(self, in_dict: dict) -> None:
        if not self.connected:
            self.connect()
        # Получение сырых модбас данных для передачи
        data = self.parser.parse_data_to_modbus(in_dict)
        # Если есть данные и некоторые расположены непоследовательно, тогда несколько итераций записи (coils)
        if data["coils"] is not None:
            for addr, value in data["coils"].items():
                self.device.coils_write(addr, value)
        # Тоже для (registers)
        if data["registers"] is not None:
            for addr, value in data["registers"].items():
                self.device.registers_write(addr, value)
