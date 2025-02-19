import pymodbus.client as ModbusClient
from pymodbus import ExceptionResponse, ModbusException
from datetime import datetime
from logging import Logger, getLogger


class Modbus:
    def __init__(self, host: str, port: int, logger: Logger | None = None) -> None:
        self.host = host
        self.port = port
        self.client = ModbusClient.ModbusTcpClient(host, port=port)
        self.logger = logger if logger is not None else getLogger(__name__)

    def coils_read(self, addr, count) -> list[bool]:
        try:
            rr = self.client.read_coils(addr, count)
        except ModbusException as exc:
            message = f"Received ModbusException({exc}) from library, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        elif isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        else:
            return rr.bits

    def input_bits(self, addr, count) -> list[bool]:
        try:
            rr = self.client.read_discrete_inputs(addr, count)
        except ModbusException as exc:
            message = f"Received ModbusException({exc}) from library, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        elif isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        else:
            return rr.bits

    def holding_registers_read(self, addr, count) -> list[int]:
        try:
            rr = self.client.read_holding_registers(addr, count)
        except ModbusException as exc:
            message = f"Received ModbusException({exc}) from library, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        elif isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        else:
            return rr.registers

    def input_registers_read(self, addr, count) -> list[int]:
        try:
            rr = self.client.read_input_registers(addr, count)
        except ModbusException as exc:
            message = f"Received ModbusException({exc}) from library, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        elif isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        else:
            return rr.registers

    def registers_write(self, addr, values) -> None:
        try:
            rr = self.client.write_registers(addr, values)
        except ModbusException as exc:
            message = f"Received ModbusException({str(exc)}) from library, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}), date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)

    def coils_write(self, addr, values) -> None:
        try:
            rr = self.client.write_coils(addr, values)
        except ModbusException as exc:
            message = f"Received ModbusException({exc}) from coils_write, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        if rr.isError():
            message = f"Received Modbus library error({rr}) from coils_write, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)
        elif isinstance(rr, ExceptionResponse):
            message = f"Received Modbus library exception ({rr}) from coils_write, date:{datetime.now().isoformat()}"
            self.logger.error(message)
            self.client.close()
            raise ConnectionError(message)

