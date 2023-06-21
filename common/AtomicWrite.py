import os
import time
import json

def split_file(filename):
    file_dir = os.path.dirname(filename)
    if not os.path.isdir(file_dir):
        if len(file_dir) > 0:
            file_dir = "./"+file_dir
        if not os.path.isdir(file_dir):
            file_dir = "."
    file_name = os.path.basename(filename)

    return file_dir, file_name


def atomic_write(filename, data, encoding="utf-8"):
    file_dir, file_name = split_file(filename)

    temp_name = f"{file_dir}/temp.txt"
    with open(temp_name, "w", encoding=encoding) as temp_file:
        temp_file.write(data)

    current_time = str(time.time())

    new_file = f"{current_time}_{file_name}"
    new_name = f"{file_dir}/{new_file}"

    # Si se cae aca -> Queda en Temporal
    os.rename(temp_name, new_name)

    #Si se cae aca -> Quedan 2 versiones (eventualmente se borraran)

    for file in os.listdir(file_dir):
        if file != new_file and file.find(file_name) > 0:
            real_file = f"{file_dir}/{file}"
            os.remove(real_file)


def get_current_file(filename):
    file_dir, file_name = split_file(filename)

    max = 0
    max_file = None

    for file in os.listdir(file_dir):
        if file.find(file_name) > 0:
            time = file.split("_")[0]
            try:
                time = float(time)
            except:
                continue
            if time > max:
                max = time
                max_file = f"{file_dir}/{file}"

    return max_file

def load_memory(filename, encoding="utf-8"):
    file = get_current_file(filename)
    print(f"FILE: {file}")
    if not file:
        return {}
    
    with open(file, "r", encoding=encoding) as f:
        return json.load(f)




# if __name__ == "__main__":
#     try:
#         atomic_write("test.txt", "Hola!")
#         print(get_current_file("test.txt"))
#     except Exception as err:
#         print("Error")
#         print(err)
#     exit = input("Exit")