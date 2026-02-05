#Made by integrator942
#Blemish pixel structure classifier
import struct
import numpy as np
from collections import deque
import os
import xml.etree.ElementTree as ET_  # Сохраняем как xml
import xml.dom.minidom
import re
import sys

dmap_folder='dmap' #Название папки в директории со скриптом, где лежат все dmap`ы
extension='.dmap' #Расширение файлов
directions_list = [                    #Связность 8
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

def find_connected_components(image):
    def_pix_counter = 0 #Счётчик дефектных пикселей
    #Нахождение связных компонент (8-связность)
    rows, cols = image.shape
    visited = np.zeros_like(image, dtype=bool)
    components = []

    for i in range(rows):
        for j in range(cols):
            if image[i, j] == 0 and not visited[i, j]:
                def_pix_counter += 1
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

    min_x: int = np.min(x_coords)
    max_x: int = np.max(x_coords)
    min_y: int = np.min(y_coords)
    max_y: int = np.max(y_coords)

    width = max_x - min_x + 1
    height = max_y - min_y + 1 #Прямоугольные размеры кластера

    bbox_area = width * height #Размер прямоугольника

    isolated_pixel_counter = isolated_pixel_counter_function(component, size) #Сколько изолированных пикселей в компоненте

    return size, width, height, bbox_area, isolated_pixel_counter


def isolated_pixel_counter_function(component, size):
    component_set = set(component) # Преобразуем компонент в множество для O(1) поиска
    pixel_counter = 0
    for j in range(size):
        x, y = component[j]
        counter = 0
        for dx, dy in directions_list:
            if (x + dx, y + dy) in component_set:
                counter += 1
        if counter == 8:
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
        'Large spot defect': 0
    }
    small_row_column = []
    for j in range(len(components)):
        classified = False
        component = components[j]
        size, width, height, bbox_area, isolated_pixel_counter = analyze_shape(component)
        dict_component['Isolated defective pixels'] += isolated_pixel_counter
        if size == 1 and classified==False: # Точка (1 пиксель)
            dict_component['Point pixel defect'] += 1
            classified = True

        if size <= 5 and isolated_pixel_counter==0 and width != 1 and height != 1 and classified==False: # Дефект Small Cluster; width==1 - столбец, height==1 - строка
            dict_component['Cluster defect']['Small'] += 1
            classified = True

        if size <= 15 and isolated_pixel_counter <= 2 and width != 1 and height != 1 and classified==False: # Дефект Medium Cluster
            dict_component['Cluster defect']['Medium'] += 1
            classified = True

        if size <= 25 and isolated_pixel_counter <= 3 and width != 1 and height != 1 and classified==False: # Дефект Large Cluster
            dict_component['Cluster defect']['Large'] += 1
            classified = True

        if size >= 26 and bbox_area<=400 and width != 1 and height != 1 and classified==False: # Дефект Spot Cluster
            dict_component['Spot defect'] += 1
            classified = True

        if not classified and width != 1 and height != 1:
            dict_component['Large spot defect'] += 1
            classified = True

        if not classified:
            small_row_column.append(component)

    return dict_component, small_row_column


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
            element = ET_.SubElement(parent, safe_key)

            if isinstance(value, dict):
                _dict_to_xml(element, value)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET_.SubElement(element, 'item')
                    if isinstance(item, dict):
                        _dict_to_xml(item_elem, item)
                    else:
                        item_elem.text = str(item)
            else:
                element.text = str(value)

    root = ET_.Element(root_tag)
    _dict_to_xml(root, dictionary)
    return ET_.ElementTree(root)

def get_dir_dmap(): #Получить список с путями к dmap`ам и размер из названия, если есть
    size_detector=[] #список со всеми параметрами каждого детекторы. РазмерX, размерY, TFT/CMOS, серийный номер
    pattern_serial=r'(\d{8})' #Регулярное выражение для поиска серийного номера
    archive_pattern=r'archive' #Регулярное выражение для архива
    pattern = r'(\d{3,4})[_x](\d{3,4})' #Для записи размеров детектора 4608x5888. Может быть и 3 на 3 числа r'(\d+)_(\d+)'. если хотим 4 на 4, то вот: r'(\d{4})x(\d{4})'
    path = []  # Список для путей файла
    if getattr(sys, 'frozen', False): #Проверка, как запущен скрипт. Это для .exe исполнения
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    files_folder = os.path.join(script_dir, dmap_folder)  # название папки, где dmap ы лежат
    if os.path.exists(files_folder) and os.path.isdir(files_folder):  # Проверяем, существует ли папка и является ли она папкой
        for root, dirs, files in os.walk(files_folder):  # Обрабатываем все файлы в папке, в т.ч. вложенные папки
            for filename in files: #Для всех найденных файлов
                if filename.lower().endswith(extension): #Если оканчивается на extension
                    full_path=os.path.join(root, filename) #Полный путь к файлу
                    if not re.search(archive_pattern, full_path, re.IGNORECASE): #Если нет паттерна архива
                        match = re.search(pattern, full_path, re.IGNORECASE) #Ищем паттерн размеров
                        if match: #Если нашёл размеры
                            width_f = int(match.group(1))
                            height_f = int(match.group(2))
                            match1 = re.findall(pattern_serial, full_path, re.IGNORECASE)  # Ищем паттерн серйиного номера, 8 цифр подряд
                            if match1:
                                serial_number = "_".join(str(x) for x in match1)
                                if len(match1)==2:
                                    if match1[0]==match1[1]:
                                        serial_number=match1[0]
                            else:
                                serial_number = 'Serial_None'
                                print('В пути', full_path,'нет серийного номера')
                            if width_f==4608 and height_f==5888:
                                size_detector.append((width_f, height_f, 'CMOS', serial_number))
                                path.append(full_path)
                            elif width_f==2816 and height_f==3584:
                                size_detector.append((width_f, height_f, 'TFT', serial_number))
                                path.append(full_path)
                            elif width_f==3480 and height_f==4352:
                                size_detector.append((width_f, height_f, 'TFT', serial_number))
                                path.append(full_path) #Другие размеры не обрабатываем
                        else: #Не нашёл размеры
                            print('В пути', full_path,'нет размеров. Добавьте размер в формате AAAAxBBBB в путь или в название, обработка будет по CMOS')
                            size_detector.append((0, 0, 'None', 'Serial_None'))
                            path.append(full_path)
    else:
        print('Папка dmap не найдена')
        exit(1)
    return path, size_detector, files_folder

def image_save(obj_, results_path_, size_detector):
    from PIL import Image  # Экспорт изображения для его просмотра
    image_normalized = (obj_ * 65535).astype(np.uint16)
    img = Image.fromarray(image_normalized).convert('I;16B')  # Сохраняем как 16-битное изображение
    os.makedirs(results_path_, exist_ok=True)
    i=0
    tiff_path = results_path_ + str(size_detector[0])+'_'+str(size_detector[1])+'_'+size_detector[2]+'_'+size_detector[3]
    if os.path.exists(tiff_path + '.tiff'):
        i += 1
        while True:
            if os.path.exists(tiff_path + '_' + str(i) + '.tiff'):
                i += 1
            else:
                img.save(tiff_path + '_' + str(i) + '.tiff')
                print('     Файл', tiff_path + '_'+str(i) + '.tiff', 'сохранён')
                break
    else:
        img.save(tiff_path + '.tiff')
        print('     Файл', tiff_path + '.tiff', 'сохранён')

def xml_export(blemish, results_path_, size_detector):
    xml_path = results_path_ + str(size_detector[0])+'_'+str(size_detector[1])+'_'+size_detector[2]+'_'+size_detector[3]
    tree = dict_to_xml_safe(blemish, 'Blemish_type')
    xml_str = ET_.tostring(tree.getroot(),
                          encoding='utf-8',
                          method='xml')
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n')
                            if line.strip() != ''])
    i = 0
    if os.path.exists(xml_path + '.xml'):
        i += 1
        while True:
            if os.path.exists(xml_path + '_' + str(i) + '.xml'):
                i += 1
            else:
                break
    if i == 0:
        with open(xml_path + '.xml', 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        path=xml_path + '.xml'
    else:
        with open(xml_path + '_' + str(i) + '.xml', 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        path=xml_path + '_' + str(i) + '.xml'
    return path


def classify_small_row(row_col, blemish_dict, det_type):
    small_rows=0
    small_cols=0

    if det_type=='CMOS':
        for rr in range(len(row_col)):
            component = row_col[rr]
            classified = False

            if len(component) <= 6 and component[0][0]==component[-1][0] and classified == False:  # Дефект Small Cluster, строка
                blemish_dict['Cluster defect']['Small'] += 1
                classified = True
                small_rows += 1

            if len(component) <= 20 and component[0][0]==component[-1][0] and classified == False:  # Дефект Medium Cluster, строка
                blemish_dict['Cluster defect']['Medium'] += 1
                classified = True
                small_rows += 1

            if len(component) <= 58 and component[0][0]==component[-1][0] and classified == False:  # Дефект Large Cluster, строка. Тут берём < 0.15 * a/2/6, где a - размер детектора
                blemish_dict['Cluster defect']['Large'] += 1
                classified = True
                small_rows += 1

            if len(component) <=346 and component[0][0] == component[-1][0] and classified == False:  # Дефект Spot Cluster, строка. Тут берём 346
                blemish_dict['Spot defect'] += 1
                classified = True
                small_rows += 1

            if not classified:  # Дефект Small Column
                small_cols += 1

    if det_type == 'TFT':
        for rr in range(len(row_col)):
            component = row_col[rr]
            classified = False

            if len(component) <= 10 and component[0][0] == component[-1][0] and classified == False:  # Дефект Small Cluster, строка
                blemish_dict['Cluster defect']['Small'] += 1
                classified = True
                small_rows += 1

            if len(component) <= 50 and component[0][0] == component[-1][0] and classified == False:  # Дефект Medium Cluster, строка
                blemish_dict['Cluster defect']['Medium'] += 1
                classified = True
                small_rows += 1

            if len(component) <= 100 and component[0][0] == component[-1][0] and classified == False:  # Дефект Large Cluster, строка. Тут берём < 0.15 * a/2/6, где a - размер детектора
                blemish_dict['Cluster defect']['Large'] += 1
                classified = True
                small_rows += 1

            if len(component) <= 422 and component[0][0] == component[-1][0] and classified == False:  # Дефект Spot Cluster, строка. Тут берём 346
                blemish_dict['Spot defect'] += 1
                classified = True
                small_rows += 1

            #Столбцы для TFT
            # if len(component) <= 10 and component[0][1] == component[-1][1] and classified == False:  # Дефект Small Cluster, строка
            #     blemish_dict['Cluster defect']['Small'] += 1
            #     classified = True
            #     small_cols += 1
            #
            # if len(component) <= 50 and component[0][1] == component[-1][1] and classified == False:  # Дефект Medium Cluster, строка
            #     blemish_dict['Cluster defect']['Medium'] += 1
            #     classified = True
            #     small_cols += 1
            #
            # if len(component) <= 100 and component[0][1] == component[-1][1] and classified == False:  # Дефект Large Cluster, строка. Тут берём < 0.15 * a/2/6, где a - размер детектора
            #     blemish_dict['Cluster defect']['Large'] += 1
            #     classified = True
            #     small_cols += 1

            if not classified:  # Дефект Spot Cluster, строка. Тут берём 346
                #blemish_dict['Spot defect'] += 1
                small_cols += 1

    return blemish_dict, small_rows, small_cols

def j_blemish_analyze_row(j_blemish, dict_row_col):
    if len(j_blemish) == 1:
        dict_row_col['Row Defect']['Single'] += 1
        j_blemish.pop(0)

    if len(j_blemish) == 2:
        if abs(j_blemish[1] - j_blemish[0]) <= 3:
            dict_row_col['Row Defect']['Double'] += 1
            j_blemish.pop(0)
            j_blemish.pop(0)
        else:
            dict_row_col['Row Defect']['Single'] += 2
            j_blemish.pop(0)
            j_blemish.pop(0)

    while j_blemish:  # Если длина 3 и больше
        if abs(j_blemish[0] - j_blemish[1]) <= 3:
            if abs(j_blemish[1] - j_blemish[2]) <= 3:
                dict_row_col['Row Defect']['Triple'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
                j_blemish.pop(0)
            else:
                dict_row_col['Row Defect']['Double'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
        else:
            dict_row_col['Row Defect']['Single'] += 1
            j_blemish.pop(0)
        if len(j_blemish) == 1:
            dict_row_col['Row Defect']['Single'] += 1
            j_blemish.pop(0)
        if len(j_blemish) == 2:
            if abs(j_blemish[1] - j_blemish[0]) <= 3:
                dict_row_col['Row Defect']['Double'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
            else:
                dict_row_col['Row Defect']['Single'] += 2
                j_blemish.pop(0)
                j_blemish.pop(0)
    return dict_row_col

def j_blemish_analyze_col(j_blemish, dict_row_col):
    if len(j_blemish) == 1:
        dict_row_col['Column Defect']['Single'] += 1
        j_blemish.pop(0)

    if len(j_blemish) == 2:
        if abs(j_blemish[1] - j_blemish[0]) <= 3:
            dict_row_col['Column Defect']['Double'] += 1
            j_blemish.pop(0)
            j_blemish.pop(0)
        else:
            dict_row_col['Column Defect']['Single'] += 2
            j_blemish.pop(0)
            j_blemish.pop(0)

    while j_blemish:  # Если длина 3 и больше
        if abs(j_blemish[0] - j_blemish[1]) <= 3:
            if abs(j_blemish[1] - j_blemish[2]) <= 3:
                dict_row_col['Column Defect']['Triple'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
                j_blemish.pop(0)
            else:
                dict_row_col['Column Defect']['Double'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
        else:
            dict_row_col['Column Defect']['Single'] += 1
            j_blemish.pop(0)
        if len(j_blemish) == 1:
            dict_row_col['Column Defect']['Single'] += 1
            j_blemish.pop(0)
        if len(j_blemish) == 2:
            if abs(j_blemish[1] - j_blemish[0]) <= 3:
                dict_row_col['Column Defect']['Double'] += 1
                j_blemish.pop(0)
                j_blemish.pop(0)
            else:
                dict_row_col['Column Defect']['Single'] += 2
                j_blemish.pop(0)
                j_blemish.pop(0)
    return dict_row_col

def determine_rows_cols(obj_, det_size_type, row_col, blemish_dict):
    dict_row_col = {
        'Row Defect': {'Single': 0,
                           'Double': 0,
                          'Triple': 0,
                       'Small Row Defects': 0},
        'Column Defect': {'Single': 0,
                           'Double': 0,
                          'Triple': 0,
                          'Small Column Defects': 0}
    }

    rows, cols = obj_.shape
    if det_size_type[2] == 'CMOS': #Если КМОП
    #1 верхний левый и нижний левый сегмент. "Строки"
        j_blemish = [] #j координаты плохих линий
        for i_rows in range(1, rows-1):
            row=[]
            for j_cols in range(1, (cols-1)//2):
                row.append(obj_[i_rows, j_cols])
            blemish_flag=row_col_analyze(row)
            if blemish_flag:
                j_blemish.append(i_rows) #Если плохая линия, то записываем её координату j

        if j_blemish: #Если непусто
            j_blemish_set=set(j_blemish)
            for rc in range(len(row_col)): #Удаляем из row_col те строки, которые мы определили как дефектные
                if (row_col[rc][0][0] in j_blemish_set) and (row_col[rc][0][0]==row_col[rc][-1][0]): #есть ли строка и является ли компонент строкой
                    l=0
                    max_l=len(row_col[rc])
                    counter=0
                    while l != max_l:
                        if row_col[rc][counter][1] < (cols-1)//2: #Если попадаем в искомую область, то
                            del(row_col[rc][counter])
                            l += 1
                        else:
                            counter += 1
                            l += 1
        row_col = [item for item in row_col if item] #Удаляем пустые списки
        dict_row_col=j_blemish_analyze_row(j_blemish, dict_row_col) #Анализируем на row defects
        #2 верхний правый и нижний правый сегмент. "Строки"

        j_blemish = []  # j координаты плохих линий
        for i_rows in range(1, rows-1):
            row = []
            for j_cols in range((cols-1)//2, cols-1):
                row.append(obj_[i_rows, j_cols])
            blemish_flag = row_col_analyze(row)
            if blemish_flag:
                j_blemish.append(i_rows)  # Если плохая линия, то записываем её координату

        if j_blemish: #Если непусто
            j_blemish_set = set(j_blemish)
            for rc in range(len(row_col)):  # Удаляем из row_col те строки, которые мы определили как дефектные
                if (row_col[rc][0][0] in j_blemish_set) and (row_col[rc][0][0] == row_col[rc][-1][0]):  # есть ли строка и является ли компонент строкой
                    l = 0
                    max_l = len(row_col[rc])
                    counter = 0
                    while l != max_l:
                        if row_col[rc][counter][1] >= (cols - 1) // 2:  # Если попадаем в искомую область, то
                            del (row_col[rc][counter])
                            l += 1
                        else:
                            counter += 1
                            l += 1

        row_col = [item for item in row_col if item]  # Удаляем пустые списки
        dict_row_col=j_blemish_analyze_row(j_blemish, dict_row_col) #Анализируем на row defects

        #Для столбцов
        j_blemish = []  # j координаты плохих линий
        for j_cols in range(1, cols-1):
            row = []
            for i_rows in range(1, rows-1):
                row.append(obj_[i_rows, j_cols])
            blemish_flag = row_col_analyze(row)
            if blemish_flag:
                j_blemish.append(j_cols)  # Если плохая линия, то записываем её координату j

        if j_blemish: #Если непусто
            j_blemish_set = set(j_blemish)
            for rc in range(len(row_col)):  # Удаляем из row_col те столбцы, которые мы определили как дефектные
                if (row_col[rc][0][1] in j_blemish_set) and (row_col[rc][0][1] == row_col[rc][-1][1]):  # есть ли столбец и является ли столбец столбцом
                    row_col[rc].clear()
        row_col = [item for item in row_col if item]  # Удаляем пустые списки
        dict_row_col = j_blemish_analyze_col(j_blemish, dict_row_col)  # Анализируем на row defects
        blemish_dict, amount_row, amount_col = classify_small_row(row_col, blemish_dict, det_size_type[2])
        dict_row_col['Row Defect']['Small Row Defects'] += amount_row
        dict_row_col['Column Defect']['Small Column Defects'] += amount_col

    elif det_size_type[2] == 'TFT':
        #Если TFT
        j_blemish = []  # j координаты плохих линий
        for i_rows in range(1, rows - 1):
            row = []
            for j_cols in range(1, cols - 1):
                row.append(obj_[i_rows, j_cols])
            blemish_flag = row_col_analyze(row)
            if blemish_flag:
                j_blemish.append(i_rows)  # Если плохая линия, то записываем её координату j

        if j_blemish: #Если непусто удаляем из связных объектов строки, которые мы определили как дефектные
            j_blemish_set = set(j_blemish)
            for rc in range(len(row_col)):  # Удаляем из row_col те столбцы, которые мы определили как дефектные
                if (row_col[rc][0][0] in j_blemish_set) and (row_col[rc][0][0] == row_col[rc][-1][0]):  # есть ли столбец и является ли столбец столбцом
                    row_col[rc].clear()
        row_col = [item for item in row_col if item]  # Удаляем пустые списки
        dict_row_col=j_blemish_analyze_row(j_blemish, dict_row_col) #Анализируем на row defects

        #Для столбцов
        j_blemish = []  # j координаты плохих линий
        for j_cols in range(1, cols - 1):
            row = []
            for i_rows in range(1, rows - 1):
                row.append(obj_[i_rows, j_cols])
            blemish_flag = row_col_analyze(row)
            if blemish_flag:
                j_blemish.append(j_cols)  # Если плохая линия, то записываем её координату j
        if j_blemish:  # Если непусто
            j_blemish_set = set(j_blemish)
            for rc in range(len(row_col)):  # Удаляем из row_col те столбцы, которые мы определили как дефектные
                if (row_col[rc][0][1] in j_blemish_set) and (
                        row_col[rc][0][1] == row_col[rc][-1][1]):  # есть ли столбец и является ли столбец столбцом
                    row_col[rc].clear()
        row_col = [item for item in row_col if item]  # Удаляем пустые списки
        dict_row_col = j_blemish_analyze_col(j_blemish, dict_row_col)  # Анализируем на row defects)

        blemish_dict, amount_row, amount_col = classify_small_row(row_col, blemish_dict, det_size_type[2])
        dict_row_col['Row Defect']['Small Row Defects'] += amount_row
        dict_row_col['Column Defect']['Small Column Defects'] += amount_col


    blemish_dict.update(dict_row_col)
    return blemish_dict

def row_col_analyze(row_):
    defective=False
    if (row_.count(0)/len(row_)) >= 0.15:
        defective=True
    return defective

def blemish_map_builder(blemish, size):
    fl_=True
    if size[0]==0: #Если не знаем размеры
        max_value = np.max(blemish)  # Если нет в имени файла размеров
        obj_ = np.ones((max_value + 3, max_value + 3))  # +3 чтобы убрать граничные условия. Чтобы по бокам были пиксели
    else:
        max_x_detector = size[0]  # Если в имени файла есть размеры
        max_y_detector = size[1]
        obj_ = np.ones((max_x_detector + 3, max_y_detector + 3))  # +3 чтобы убрать граничные условия. Чтобы по бокам были пиксели
    try:
        for i_ in range(len(blemish)):
            obj_[blemish[i_][0] + 1][blemish[i_][1] + 1] = 0  # +1 так как граничные условия
    except IndexError: #Если dmap содержит координаты больше, чем в названии
        print('!!!!!!!!!!!dmap содержит координаты больше, чем указаны. Обработка файла выполнена не будет!!!!!!!!')
        fl_=False
    return obj_, fl_

def dmap_blemish(defects_):
    coordinates_ = []  # Список для координат битых пикселей из dmap
    defects_ = np.asarray(defects_)
    length = defects_[0]
    defects_ = defects_[1:]
    for i in range(length):
        coordinates_.append([defects_[0], defects_[1]])
        defects_ = defects_[2:]
        corr_amount = defects_[0]
        defects_ = defects_[(corr_amount * 2 + 1):]
    coordinates_ = np.asarray(coordinates_)
    return coordinates_

if __name__ == "__main__":
    bad_counter=0 #Пустые dmap или несоответствующие размерам из описания
    print('Made by integrator942, Medical Tech. Ltd.')
    print('Blemish pixel structure classifier')
    file_path, detector_size, dmap_path = get_dir_dmap() #Узнаём путь к dmap и размер из пути, и оттуда же узнаём его тип по размерам
    results_path = os.path.join(dmap_path, 'results'+ os.sep) #Создаём папку с названием results в dmap
    print('Всего найдено полноформатных dmap', dmap_folder, '-', len(file_path))
    for k in range(len(file_path)):
        defects = []  # В этот список записывается весь файл dmap
        coordinates = []  # Список для координат битых пикселей из dmap
        try:
            with open(file_path[k], "rb") as file:
                while True:
                        defects.append(struct.unpack('<i', file.read(4))[0])
        except struct.error: #Когда считали весь dmap
                if len(defects) == 0:
                    bad_counter += 1
                else:
                    coordinates = dmap_blemish(defects) #Вынимаем из dmap координаты дефектных пикселей
                    print('Файл №', k+1, file_path[k], 'прочитан')
                    obj, fl = blemish_map_builder(coordinates, detector_size[k]) #Строится карта битых пикселей
                    if fl:
                        #image_save(obj, results_path, detector_size[k]) #Сохраняем карту битых пикселей
                        #print('     Карта битых пикселей сохранена как .tiff')

                        list_components, defect_pixel_counter = find_connected_components(obj) #Возвращает лист с несвязными кластерами и общее количество дефектных пикселей
                        print('     Несвязные кластеры определены, выполняется их классификация и расчёт изолированных пикселей')

                        d, row_column_small_components = determine_shape_type(list_components) #Классификация и кластеризация

                        blemish_type = {'Total defect pixels': defect_pixel_counter}
                        blemish_type.update(d) #Словарь без RowCol
                        print('     Определяются дефектные строки и столбцы')
                        blemish_type=determine_rows_cols(obj, detector_size[k], row_column_small_components, blemish_type)
                        print('    ', blemish_type)
                        xml_save_path=xml_export(blemish_type,results_path ,detector_size[k]) #Экспорт в xml
                        print('     Сохранён xml файл с классификацией', xml_save_path + '.xml')
                    else: bad_counter += 1
        except Exception as e:
            print(f"    Другая ошибка: {e}") #Другая ошибка
    print('Все файлы обработаны')
    print('dmap пустые или с несответстующими размерами:', bad_counter)






