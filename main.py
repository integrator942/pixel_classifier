import struct
import numpy as np
import matplotlib.pyplot as plt

defects=[]
coordinates=[]

try:
    with open("DefectMap3.dmap", "rb") as file:
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
coordinates=np.asarray(coordinates)
max_value=np.max(coordinates)
obj=np.ones((max_value+1, max_value+1))
for i in range(len(coordinates)):
    obj[coordinates[i][0]][coordinates[i][1]] = 0

from PIL import Image
image_normalized = (obj * 65535).astype(np.uint16)
img = Image.fromarray(image_normalized, mode='I;16B')
img.save('DefectMap.tiff')



#from PIL import Image
#img = Image.fromarray(obj, 'I;16B')
#plt.imshow(img)
#plt.show()

