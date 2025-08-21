# to get data from Provinces.txt
class Get_Provinces_of_File:
    PROVINCE_FILE_PATH = 'provinces/province_name_list/provinces.txt'

    try:
        with open(PROVINCE_FILE_PATH, 'r', encoding='utf-8') as f:
            PROVINCES = {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        raise RuntimeError(f"Province file not found at {PROVINCE_FILE_PATH}")


