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
"""
[(3352, 1147), (3353, 1147), (3354, 1146), (3355, 1145), (3355, 1146),
(3355, 1144), (3355, 1143), (3356, 1143), (3356, 1142), (3357, 1142),   Пример компонента
(3357, 1143), (3357, 1144), (3355, 1141), (3355, 1140), (3354, 1139), (3355, 1139)]
"""
def analyze_shape(component): #Один компонент из списка компонентов
    points = np.array(component) # Координаты точек
    x_coords = points[:, 0] #Все координаты x компонента
    y_coords = points[:, 1] #Все координаты y компонента
    size = len(points)

    min_x, max_x = np.min(x_coords), np.max(x_coords)  # Минимальные и максимальные координаты
    min_y, max_y = np.min(y_coords), np.max(y_coords)

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    bbox_area = width * height # Плотность (отношение площади компонента к площади прямоугольника со сторонами width, height)
    density = size / bbox_area

    aspect_ratio = width / height # Соотношение сторон

    # Определяем тип фигуры
    shape_type = determine_shape_type(size, width, height, density, aspect_ratio)

    return {
        "type": shape_type,
        "size": size,
        "width": width,
        "height": height
    }

def determine_shape_type(size, width, height,
                          density, aspect_ratio):

    if size == 1: # Точка (1 пиксель)
        return "точка"

    if size == 4 and width == 2 and height == 2: # Маленький квадрат 2x2
        return "квадрат 2x2"

    # Квадрат или прямоугольник
    if density > 0.8:  # Высокая плотность
        if 0.9 <= aspect_ratio <= 1.1:
            return "квадрат"
        else:
            return "прямоугольник"

    # Линия
    if (width == 1 and height > 1) or (height == 1 and width > 1):
        return "линия (вертикальная/горизонтальная)"

    # Круг (приближенно)
    if 0.7 <= density <= 0.9 and 0.8 <= aspect_ratio <= 1.2:
        return "круг (приближенно)"

    # Общий случай
    if size < 10:
        return "маленькая фигура"

    return "сложная фигура"

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





#Экспорт изображения
#from PIL import Image
#image_normalized = (obj * 65535).astype(np.uint16)
#img = Image.fromarray(image_normalized, mode='I;16B') #Сохраняем как 16-битное изображение
#img.save('DefectMap4.tiff')


