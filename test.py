import struct
import numpy as np

defects=[]
coordinates=[]

try:
    with open("DefectMap4.dmap", "rb") as file:
        while True:
                defects.append(struct.unpack('<i', file.read(4))[0])
except FileNotFoundError:
    print("Файл не найден") #Нет файла
except struct.error:
    print(f"Файл прочитан") #Преобразуем пустое значение
except Exception as e:
    print(f"Файл прочитан: {e}") #Другая ошибка

defects=np.asarray(defects)
length=defects[0]
defects = defects[1:]

for i in range(length):
    coordinates.append([defects[0],defects[1]])
    defects = defects[2:]
    corr_amount=defects[0]
    defects = defects[(corr_amount * 2 + 1):]
