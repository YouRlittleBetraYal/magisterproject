import numpy as np

max_pwm = 255
max_speed = 2.55  # Максимальна швидкість у м/с = 100 мм/c

def pwm_to_speed(pwm_value):
    """Конвертує значення PWM у швидкість у м/с"""
    return (pwm_value / max_pwm) * max_speed

def fuzzification_distance(sensor_value):
    """Фазифікація для відстані до цілі (лівий датчик)"""
    ranges = [
    [0.06, 0.30, 0.30, 0.60,],  # SLD
    [0.30, 0.60, 0.60, 1.0,],  # ALD
    [0.60, 0.99, 0.99, 1.0]  # BLD
]
    
    categories = ["SLD", "ALD", "BLD"]
    membership_values = [0] * len(ranges)

    for i, range_set in enumerate(ranges):
        a, b, c, d = range_set
        if a <= sensor_value < b:
            membership_values[i] = (sensor_value - a) / (b - a)  # Зростання до 1
        elif b <= sensor_value <= c:
            membership_values[i] = 1  # Максимум
        elif c < sensor_value <= d:
            membership_values[i] = (d - sensor_value) / (d - c)  # Спадання до 0
        elif sensor_value > d:
            membership_values[i] = 0  # Поза межами

    return dict(zip(categories, membership_values))

def fuzzification_right(sensor_value, threshold=0.5):
    """Фазифікація для правого датчика (кут) """
    ranges = [
    [0.06, 0.30, 0.30, 0.60,],  # SRD
    [0.30, 0.60, 0.60, 1.00,],  # ARD
    [0.60, 0.99, 0.99, 1.00]  # BRD
]
 
    
    categories = ["SRD", "ARD", "BRD"]
    membership_values = [0] * len(ranges)

    for i, range_set in enumerate(ranges):
        a, b, c, d = range_set
        if a <= sensor_value < b:
            membership_values[i] = (sensor_value - a) / (b - a)  # Зростання до 1
        elif b <= sensor_value <= c:
            membership_values[i] = 1  # Максимум
        elif c < sensor_value <= d:
            membership_values[i] = (d - sensor_value) / (d - c)  # Спадання до 0
        elif sensor_value > d:
            membership_values[i] = 0  # Поза межами

    return dict(zip(categories, membership_values))

def pwm_membership(speed):
    """Визначає належність для категорій швидкості PWM."""
    ranges = {
        "VLS": [1.0, 2.0, 2.0, 25.0],
        "LS": [2.0, 25.0, 25.0, 50.0],
        "AS": [25.0, 50.0, 50.0, 75.0],
        "BS": [50.0, 75.0, 75.0, 99.0],
        "VBS": [75.0, 75.0, 99.0, 100.0]
    }
    
    membership_values = {}
    
    for category, (a, b, c, d) in ranges.items():
        if a <= speed < b:
            membership_values[category] = (speed - a) / (b - a)
        elif b <= speed <= c:
            membership_values[category] = 1
        elif c < speed <= d:
            membership_values[category] = (d - speed) / (d - c)
        else:
            membership_values[category] = 0
    
    return membership_values

# Дефазифікація на основі Мамдані
def defuzzification(rules_outputs):
    """Дефазифікація значень PWM на основі правил Мамдані."""
    numerator = 0
    denominator = 0

    # Виконуємо агрегацію значень вихідних членських функцій
    for category, output in rules_outputs.items():
        # Визначаємо центр трапеції для кожної категорії
        if category == "VLS":
            center = 0.0
        elif category == "LS":
            center = 25.0
        elif category == "AS":
            center = 50.0
        elif category == "BS":
            center = 75.0
        elif category == "VBS":
            center = 100.0
        else:
            center = 0

        # Додаємо зважені значення для чисельника і знаменника
        numerator += output * center
        denominator += output

    # Уникаємо ділення на нуль
    if denominator == 0:
        return 0
    else:
        return numerator / denominator
    
# Основна нечітка логіка
def fuzzy_logic(distance, angle):
    left_membership = fuzzification_distance(distance)
    right_membership = fuzzification_right(angle)

    # Початкові значення PWM для коліс (словники)
    rules_outputs_left = {"VLS": 0, "LS": 0, "AS": 0, "BS": 0, "VBS": 0}
    rules_outputs_right = {"VLS": 0, "LS": 0, "AS": 0, "BS": 0, "VBS": 0}

    # Виведення значень належності
    print("Distance Membership:", left_membership)
    print("Angle Membership:", right_membership)

    # Застосування правил
##IF SLD
    if all(value == 0 for value in left_membership.values()) and all(value == 0 for value in right_membership.values()):
        print("No obstacles detected, moving straight!")
        # Рух прямо (однакова швидкість для обох коліс)
        rules_outputs_left["VBS"] = 1  # Наприклад, максимальна швидкість
        rules_outputs_right["VBS"] = 1

    else:
        print("object detected")
        # Якщо є перешкоди, активуємо інші правила
        # Правила для лівого датчика (SLD, ALD, BLD)
        if left_membership["SLD"] > 0:
            rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], left_membership["SLD"])
            rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], left_membership["SLD"])

        if left_membership["ALD"] > 0:
            rules_outputs_left["BS"] = max(rules_outputs_left["BS"], left_membership["ALD"])
            rules_outputs_right["LS"] = max(rules_outputs_right["LS"], left_membership["ALD"])

        if left_membership["BLD"] > 0:
            rules_outputs_left["AS"] = max(rules_outputs_left["AS"], left_membership["BLD"])
            rules_outputs_right["LS"] = max(rules_outputs_right["LS"], left_membership["BLD"])

        # Правила для правого датчика (SRD, ARD, BRD)
        if right_membership["SRD"] > 0:
            rules_outputs_left["VLS"] = max(rules_outputs_left["LS"], right_membership["SRD"])
            rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["SRD"])

        if right_membership["ARD"] > 0:
            rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["ARD"])
            rules_outputs_right["BS"] = max(rules_outputs_right["BS"], right_membership["ARD"])

        if right_membership["BRD"] > 0:
            rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["ARD"])
            rules_outputs_right["AS"] = max(rules_outputs_right["AS"], right_membership["ARD"])

    # Дефазифікація
    left_pwm = defuzzification(rules_outputs_left)
    right_pwm = defuzzification(rules_outputs_right)

    # Виведення PWM значень
    print("Left PWM after defuzzification:", left_pwm)
    print("Right PWM after defuzzification:", right_pwm)

    return left_pwm, right_pwm
