import yaml
from app.device_handler import ControllerHandler


if __name__ == "__main__":
    try:
        with open("config/settings.yml", "r") as file:
            conf = yaml.safe_load(file)

        controller = ControllerHandler(conf)
        # Получение.
        # Прием и парсинг принятых данных
        received_data = controller.receive()
        print(received_data)
        # Отправка.
        # Данные на отправку
        trans_data = {
            "varBit0": False,
            "varBit3": True,
            "varReg0": 325,
            "varReg1": 0,
            "varReg3": -1001,
            "varReg4": -10,
            "varReg5": 64565464646566566,
        }
        # Парсинг словаря и передача на устройство
        controller.transmit(trans_data)
        # Закрытие сокета, если не в цикле
        controller.close_connect()
    except KeyboardInterrupt:
        print("Опрос остановлен пользователем")
