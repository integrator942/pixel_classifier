import os
file_path=[]
script_dir = os.path.dirname(os.path.abspath(__file__)) #Путь к скрипту
files_folder = os.path.join(script_dir, 'dmap')  # название папки, где dmap ы лежат
if os.path.exists(files_folder) and os.path.isdir(files_folder):      # Проверяем, существует ли папка и является ли она папкой
    for filename in os.listdir(files_folder): # Обрабатываем все файлы в папке
        file_path.append(os.path.join(files_folder, filename))
print(file_path)
