import struct
import numpy as np
from collections import deque
import os
import xml.etree.ElementTree as ET  # Сохраняем как xml
import xml.dom.minidom
import re

dmap_folder='dmap' #Название папки в директории со скриптом, где лежат все dmap`ы
extension='.dmap' #Расширение файлов
directions_list = [                    #Связность 8
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
    dict_component = {
        'Isolated defective pixels': 0,
        'Point pixel defect': 0,
        'Cluster defect': {'Small': 0,
                           'Medium': 0,
                           'Large': 0},
        'Spot defect': 0,
    }

    # dict_component={
    #     'Isolated defective pixels': 0, #Если хотим Row defect
    #     'Point pixel defect': 0,
    #     'Cluster defect': {'Small': 0,
    #                        'Medium': 0,
    #                        'Large': 0},
    #     'Spot defect': 0,
    #     'Row defect': 0,
    # }

    for j in range(len(components)):
        classified = False
        component = components[j]

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
            #dict_component['Row defect'] += 1 #Row defect в другом месте будут
            classified = True

        if not classified: # Дефект Spot Cluster
            dict_component['Spot defect'] += 1

    return dict_component


def dict_to_xml_safe(dictionary, root_tag='root'):
    """Безопасная конвертация словаря в XML с валидацией имен тегов"""

    def sanitize_tag(tag):
        """Очищает имя тега от недопустимых символов"""
        # Заменяем недопустимые символы
        tag = str(tag).replace(' ', '_').replace('(', '').replace(')', '')
        tag = tag.replace('@', '').replace('$', '').replace('#', '')
        # Тег не может начинаться с цифры
        if tag and tag[0].isdigit():
            tag = 'item_' + tag
        return tag

    def _dict_to_xml(parent, dict_obj):
        for key, value in dict_obj.items():
            safe_key = sanitize_tag(key)
            element = ET.SubElement(parent, safe_key)

            if isinstance(value, dict):
                _dict_to_xml(element, value)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET.SubElement(element, 'item')
                    if isinstance(item, dict):
                        _dict_to_xml(item_elem, item)
                    else:
                        item_elem.text = str(item)
            else:
                element.text = str(value)

    root = ET.Element(root_tag)
    _dict_to_xml(root, dictionary)
    return ET.ElementTree(root)

def get_dir_dmap(): #Получить список с путями к dmap`ам
    size_detector=[]
    pattern = r'(\d+)x(\d+)' #Для записи размеров детектора 4608x5888. Может быть и 3 на 3 числа. если хотим 4 на 4, то вот: r'(\d{4})x(\d{4})'
    path = []  # Список для путей файла
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к скрипту
    files_folder = os.path.join(script_dir, dmap_folder)  # название папки, где dmap ы лежат
    if os.path.exists(files_folder) and os.path.isdir(files_folder):  # Проверяем, существует ли папка и является ли она папкой
        for filename in os.listdir(files_folder):  # Обрабатываем все файлы в папке
            if filename.lower().endswith(extension):
                path.append(os.path.join(files_folder, filename))
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    width_f = int(match.group(1))
                    height_f = int(match.group(2))
                    size_detector.append((width_f, height_f))
                else:
                    print('В имени файла нет размеров, обработка будет некорректная. Добавьте размер в формате AAAAxBBBB в имя файла')
                    size_detector.append(None)
    return path, size_detector

def image_save(obj_, path):
    from PIL import Image  # Экспорт изображения для его просмотра
    image_normalized = (obj_ * 65535).astype(np.uint16)
    img = Image.fromarray(image_normalized).convert('I;16B')  # Сохраняем как 16-битное изображение
    tiff_path = path.rstrip('.dmap')
    img.save(tiff_path + '.tiff')  # Сохраняем в ту же папку, где и был dmap

def xml_export(blemish, path):
    xml_path = path.rstrip('.dmap')
    tree = dict_to_xml_safe(blemish, 'Blemish_type')
    xml_str = ET.tostring(tree.getroot(),
                          encoding='utf-8',
                          method='xml')
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n')
                            if line.strip() != ''])
    with open(xml_path + '.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    return xml_path + '.xml'

if __name__ == "__main__":
    file_path, detector_size = get_dir_dmap()
    print('Всего файлов в папке dmap -', len(file_path))
    for k in range(len(file_path)):
        defects = []  # В этот список записывается весь файл dmap
        coordinates = []  # Список для координат битых пикселей из dmap
        try:
            with open(file_path[k], "rb") as file:
                while True:
                        defects.append(struct.unpack('<i', file.read(4))[0])
        except struct.error: #Когда считали весь dmap
            print('Файл №', k+1, 'прочитан')
            defects = np.asarray(defects)
            length = defects[0]
            defects = defects[1:]
            for i in range(length):
                coordinates.append([defects[0], defects[1]])
                defects = defects[2:]
                corr_amount = defects[0]
                defects = defects[(corr_amount * 2 + 1):]
            coordinates = np.asarray(coordinates)
            if not detector_size[k]:
                max_value = np.max(coordinates) #Если нет в имени файла размеров
                obj = np.ones((max_value + 2, max_value + 2))  # +2 чтобы убрать граничные условия. Чтобы по бокам были пиксели
            else:
                max_x_detector = detector_size[k][0] #Если в имени файла есть размеры
                max_y_detector = detector_size[k][1]
                obj = np.ones((max_x_detector + 2, max_y_detector + 2))  # +2 чтобы убрать граничные условия. Чтобы по бокам были пиксели
            for i in range(len(coordinates)):
                obj[coordinates[i][0] + 1][coordinates[i][1] + 1] = 0  # +1 так как граничные условия
            image_save(obj, file_path[k]) #Сохраняем карту битых пикселей
            print('Карта битых пикселей сохранена как .tiff')
            list_components, defect_pixel_counter = find_connected_components(obj) #Возвращает лист с несвязными кластерами и общее количество дефектных пикселей
            print('Несвязные кластеры определены, выполняется их классификация')
            d = determine_shape_type(list_components) #Классификация и кластеризация
            Blemish_type = {'Total defect pixels': defect_pixel_counter}
            Blemish_type.update(d)
            print(Blemish_type)
            xml_save_path=xml_export(Blemish_type, file_path[k]) #Экспорт в xml
            print('Сохранён xml файл с классификацией')
        except Exception as e:
            print(f"Другая ошибка: {e}") #Другая ошибка
    print('Все файлы обработаны')






