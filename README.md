# modbus-grabber

#### Читает и записывает данные по протоколу modbus TCP
```
Пример приема из modbus slave:
{'READ_INPUT_DATA': {  # Значения из discrete input и input registers
    'varBit0': False,
    'varBit1': False,
    'varBit2': True,
    'varBit3': True,
    'varBit4': False,
    'varBit5': True,
    'varReg0': 111,
    'varReg1': 222,
    'varReg2': 333,
    'varReg3': 444,
    'varReg4': 555,
    'varReg5': 36.6,
    }, 
 'READ_OUTPUT_DATA': {  # Значения из coils и holding registers
    'varBit0': False,
    'varBit1': False,
    'varBit2': False,
    'varBit3': True,
    'varBit4': False,
    'varBit5': True,
    'varReg0': 325,
    'varReg1': 0,
    'varReg2': 13,
    'varReg3': -1001,
    'varReg4': -36.6,
    'varReg5': 100500100500},
    }
}

Для передачи можно взять словарь 'READ_OUTPUT_DATA' и передать один или несколько ключей со значениями
```