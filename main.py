import struct
import numpy as np
import matplotlib.pyplot as plt

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
coordinates=np.asarray(coordinates)
max_value=np.max(coordinates)
obj=np.ones((max_value+1, max_value+1))
for i in range(len(coordinates)):
    obj[coordinates[i][0]][coordinates[i][1]]=0
print(obj)






"""
# Создаем цветовую карту: 0 -> красный, 1 -> черный
from matplotlib import colors
cmap = colors.ListedColormap(['red', 'black'])

plt.figure(figsize=(6, 6))
plt.imshow(matrix, cmap=cmap, interpolation='nearest')

# Добавляем сетку и значения
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        plt.text(j, i, str(matrix[i, j]),
                ha='center', va='center',
                color='white' if matrix[i, j] == 0 else 'yellow',
                fontsize=14, fontweight='bold')

plt.title('0 = красный, 1 = черный', fontsize=14)
plt.axis('off')  # Скрыть оси
plt.show()
"""

