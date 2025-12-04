import struct
import numpy as np
from collections import deque

way="DefectMap3.dmap"

directions_list = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

def find_connected_components(image):
    def_pix_counter = 0
    #Нахождение связных компонент (8-связность)
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
                            queue.append((nx, ny)) #Если пиксель черные и мы его не сещали - записываем в очередь
                            def_pix_counter += 1
                components.append(component)
    return components, def_pix_counter  #Список списков кортежей с координатами черных пикселей, объединены по связности 8

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
    height = max_y - min_y + 1 #Прямоугольные размеры кластера

    bbox_area = width * height #Размер прямоугольника

    isolated_pixel_counter = isolated_pixel_counter_function(component, size) #Сколько изолированных пикселей в компоненте

    return size, width, height, bbox_area, isolated_pixel_counter

def isolated_pixel_counter_function(component, size):
    pixel_counter = 0  # Счётчик изолированных пикселей компонента
    for j in range(size):
        x, y = component[j]  # Записали координаты пикселя из кортежа
        counter = 0  # Счётчик для пикселей связности 8
        for dx, dy in directions_list:
            nx, ny = x + dx, y + dy
            if (nx, ny) in component:  # Если такой компонент (кортеж) есть
                counter += 1
        if counter == 8:  # Если за цикл мы насчитали 8 пикселей, то пиксель изолирован
            pixel_counter += 1
    return pixel_counter

def determine_shape_type(components):

    dict_component={
        'Isolated defective pixels': 0,
        'Point pixel defect': 0,
        'Cluster defect': {'Small': 0,
                           'Medium': 0,
                           'Large': 0},
        'Spot defect': 0,
        'Row defect': 0,
    }

    for i in range(len(components)):
        classified = False
        component=components[i]

        size, width, height, bbox_area, isolated_pixel_counter = analyze_shape(component)
        dict_component['Isolated defective pixels'] += isolated_pixel_counter

        if size == 1 and classified==False: # Точка (1 пиксель)
            dict_component['Point pixel defect'] += 1
            classified = True

        if size <= 5 and isolated_pixel_counter==0 and classified==False: # Дефект Small Cluster
            dict_component['Cluster defect']['Small'] += 1
            classified = True

        if size <= 15 and isolated_pixel_counter <= 2 and classified==False: # Дефект Medium Cluster
            dict_component['Cluster defect']['Medium'] += 1
            classified = True

        if size <= 25 and isolated_pixel_counter <= 3 and classified==False: # Дефект Large Cluster
            dict_component['Cluster defect']['Large'] += 1
            classified = True

        if size >= 16 and (width/height>=16 or height/width>=16) and classified==False:
            dict_component['Row defect'] += 1
            classified = True

        if not classified: # Дефект Spot Cluster
            dict_component['Spot defect'] += 1

    return dict_component

if __name__ == "__main__":
    defects=[]
    coordinates=[]
    try:
        with open(way, "rb") as file:
            while True:
                    defects.append(struct.unpack('<i', file.read(4))[0])
    except FileNotFoundError:
        print("Файл не найден") #Нет файла

    except struct.error:
        print(f"Файл прочитан") #Преобразуем пустое значение
        defects = np.asarray(defects)
        length = defects[0]
        defects = defects[1:]
        for i in range(length):
            coordinates.append([defects[0], defects[1]])
            defects = defects[2:]
            corr_amount = defects[0]
            defects = defects[(corr_amount * 2 + 1):]
        coordinates = np.asarray(coordinates)
        max_value = np.max(coordinates)
        obj = np.ones((max_value + 3, max_value + 3))  # +3 чтобы убрать граничные условия. Чтобы по бокам были пиксели
        for i in range(len(coordinates)):
            obj[coordinates[i][0] + 1][coordinates[i][1] + 1] = 0  # +1 так как граничные условия

        # Экспорт изображения для его просмотра
        # from PIL import Image
        # image_normalized = (obj * 65535).astype(np.uint16)
        # img = Image.fromarray(image_normalized, mode='I;16B') #Сохраняем как 16-битное изображение
        # img.save('DefectMap4.tiff')

        list_components, defect_pixel_counter = find_connected_components(obj) #Возвращает лист с несвязными кластерами и общее количество дефектных пикселей
        d = determine_shape_type(list_components)
        d1 = {'Total defect pixels': defect_pixel_counter}
        d1.update(d)
        print(d1)

    except Exception as e:
        print(f"Другая ошибка: {e}") #Другая ошибка







