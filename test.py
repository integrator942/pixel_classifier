import struct
import numpy as np
from collections import deque

def find_connected_components(image):
    #Нахождение связных компонент (8-связность)
    directions_list = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]
    rows, cols = image.shape
    visited = np.zeros_like(image, dtype=bool)
    components = []

    for i in range(rows):
        for j in range(cols):
            if image[i, j] == 0 and not visited[i, j]:
                # Начинаем новый компонент
                component = []
                queue = deque([(i, j)]) #Эта штука быстрее списка
                visited[i, j] = True
                while queue: #Пока очередь не пуста, итерируемся
                    x, y = queue.popleft() #Очищаем queue слева и записываем очищенные значения в x, y
                    component.append((x, y)) #Записываем координаты пикселя
                    for dx, dy in directions_list:
                        nx, ny = x + dx, y + dy
                        if image[nx, ny] == 0 and not visited[nx, ny]:
                            visited[nx, ny] = True
                            queue.append((nx, ny))
                components.append(component)
    return components #Список списков кортежей с координатами черных пикселей

if __name__ == "__main__":
    defects=[]
    coordinates=[]
    way="DefectMap3.dmap"
    try:
        with open(way, "rb") as file:
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
    obj=np.ones((max_value+3, max_value+3)) #+3 чтобы убрать граничные условия. Чтобы по бокам были пиксели
    for i in range(len(coordinates)):
        obj[coordinates[i][0] + 1][coordinates[i][1] + 1] = 0 #+1 так как граничные условия
    list_components=find_connected_components(obj)
print(list_components)