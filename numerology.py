# bot/numerology.py

def calculate_life_path_number(dob):
    """
    Розрахунок числа життєвого шляху на основі дати народження.
    :param dob: дата народження у форматі 'DD-MM-YYYY'
    :return: число життєвого шляху
    """
    digits = [int(char) for char in dob if char.isdigit()]
    total = sum(digits)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def calculate_expression_number(name):
    """
    Розрахунок числа вираження на основі імені.
    :param name: повне ім'я користувача
    :return: число вираження
    """
    # Піфагорійська система
    name = name.upper()
    char_to_num = {
        'A':1, 'J':1, 'S':1,
        'B':2, 'K':2, 'T':2,
        'C':3, 'L':3, 'U':3,
        'D':4, 'M':4, 'V':4,
        'E':5, 'N':5, 'W':5,
        'F':6, 'O':6, 'X':6,
        'G':7, 'P':7, 'Y':7,
        'H':8, 'Q':8, 'Z':8,
        'I':9, 'R':9
    }
    total = 0
    for char in name:
        if char in char_to_num:
            total += char_to_num[char]
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def calculate_soul_number(name):
    """
    Розрахунок числа душі на основі голосних в імені.
    :param name: повне ім'я користувача
    :return: число душі
    """
    # Піфагорійська система
    name = name.upper()
    vowels = ['A', 'E', 'I', 'O', 'U', 'Y']
    char_to_num = {
        'A':1, 'E':5, 'I':9, 'O':6, 'U':3, 'Y':7,
    }
    total = 0
    for char in name:
        if char in vowels:
            total += char_to_num.get(char, 0)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def calculate_personality_number(name):
    """
    Розрахунок числа особистості на основі приголосних в імені.
    :param name: повне ім'я користувача
    :return: число особистості
    """
    name = name.upper()
    vowels = ['A', 'E', 'I', 'O', 'U', 'Y']
    char_to_num = {
        'B':2, 'C':3, 'D':4, 'F':6, 'G':7,
        'H':8, 'J':1, 'K':2, 'L':3, 'M':4,
        'N':5, 'P':7, 'Q':8, 'R':9, 'S':1,
        'T':2, 'V':4, 'W':5, 'X':6, 'Z':8
    }
    total = 0
    for char in name:
        if char not in vowels and char.isalpha():
            total += char_to_num.get(char, 0)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def calculate_improvement_number(life_path, expression):
    """
    Розрахунок числа вдосконалення.
    :param life_path: число життєвого шляху
    :param expression: число вираження
    :return: число вдосконалення
    """
    total = life_path + expression
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total
