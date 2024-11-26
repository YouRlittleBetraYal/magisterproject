import numpy as np

max_pwm = 255 #ліміт максимального pwm
max_speed = 2.55  # Максимальна швидкість у м/с = 0.100 ммс при pwm 100

#конвертація pwm
def pwm_to_speed(pwm_value):
    """Конвертує значення PWM у швидкість у м/с"""
    return (pwm_value / max_pwm) * max_speed

#обчислення відстані МРП до цілі
def calculate_distance(robot_pos, target_pos):
    return np.sqrt((target_pos[0] - robot_pos[0])**2 + (target_pos[1] - robot_pos[1])**2)

#обчислення кута від МРП до цілі 
def calculate_angle(robot_pos, target_pos, robot_orientation):
    dx = target_pos[0] - robot_pos[0]
    dy = target_pos[1] - robot_pos[1]
    # Обчислюємо кут до цілі
    theta_t = np.arctan2(dy, dx)
    # Перетворюємо кут у градуси
    phi = np.degrees(theta_t) - robot_orientation
    # Нормалізуємо phi, щоб він був у діапазоні [-180, 180]
    phi = (phi + 180) % 360 - 180
  
    phi = float(phi)
    print("angle to target (degrees):", phi)
    return phi

#фазифікація відстані, функція належності дистанції 
# (VSD,SD,AD,BD,VBD)
#на вхід подається обчисленя дистанція до цілі
def fuzzification_distance(sensor_value):
    """Фазифікація для відстані до цілі (лівий датчик)"""
    ranges = [
    [0.500, 0.700, 0.700, 1.250],       # Дуже близько
    [0.700, 1.250, 1.250, 2.500],           # Близько
    [1.250, 2.500, 2.500, 3.750],           # Середньо
    [2.500, 3.750, 3.750, 5.000],           # Далеко
    [3.750, 4.999, 4.999, 5.000]         # Дуже далеко
]
    
    categories = ["VSD", "SD", "AD", "BD", "VBD"]
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

#фазифікація кута, функція належності кута 
# (NBA,NAA,NSA,ZA,PSA,PAA,PBA)
#на вхід подається обчислений кут до цілі
def fuzzification_right(sensor_value):
    """Фазифікація для правого датчика (кут)"""
    ranges = [
        [-180.0, -179.0, -179.0, -120.0],  # NBA
        [-179.0, -120.0, -120.0, -60.0],   # NAA
        [-120.0, -60.0, -60.0, 0.0],       # NSA
        [-60.0, 0.0, 0.0, 60.0],           # ZA
        [0.0, 60.0, 60.0, 120.0],          # PSA
        [60.0, 120.0, 120.0, 180.0],       # PAA
        [120.0, 179.0, 179.0, 180.0],      # PBA
    ]
    
    categories = ["NBA", "NAA", "NSA", "ZA", "PSA", "PAA", "PBA"]
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

#функція належності швидкостей
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

# Дефазифікація + агрегація
def defuzzification(rules_outputs):
    """Дефазифікація значень """
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

# нечітка логіка, база правил лівого/правого коліс відповідно належностям
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
##IF VSD AND PBA,PAA,PSA,ZA,NSA,NAA,NBA RULES THEN VR,VL
    if left_membership["VSD"] and right_membership["NBA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["NBA"])
        rules_outputs_right["BS"] = max(rules_outputs_right["BS"], right_membership["NBA"])

    if left_membership["VSD"] and right_membership["NAA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VBS"], right_membership["NAA"])
        rules_outputs_right["AS"] = max(rules_outputs_right["VLS"], right_membership["NAA"])

    if left_membership["VSD"] and right_membership["NSA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["NSA"])
        rules_outputs_right["LS"] = max(rules_outputs_right["LS"], right_membership["NSA"])
    
    if left_membership["VSD"] and right_membership["ZA"] > 0:
        rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["ZA"])
        rules_outputs_right["LS"] = max(rules_outputs_right["LS"], right_membership["ZA"])

    if left_membership["VSD"] and right_membership["PSA"] > 0:
        rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["PSA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["PSA"])

    if left_membership["VSD"] and right_membership["PAA"] > 0:
        rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["PAA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["PAA"])
    
    if left_membership["VSD"] and right_membership["PBA"] > 0:
        rules_outputs_left["AS"] = max(rules_outputs_left["AS"], right_membership["PBA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["PBA"])
        
    ##if SD AND PBA,PAA,PSA,ZA,NSA,NAA,NBA RULES VR,VL
    if left_membership["SD"] and right_membership["NBA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["NBA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["NBA"])

    if left_membership["SD"] and right_membership["NAA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["NAA"])
        rules_outputs_right["BS"] = max(rules_outputs_right["BS"], right_membership["NAA"])

    if left_membership["SD"] and right_membership["NSA"] > 0:
        rules_outputs_left["AS"] = max(rules_outputs_left["AS"], right_membership["NSA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NSA"])

    if left_membership["SD"] and right_membership["ZA"] > 0:
        rules_outputs_left["LS"] = max(rules_outputs_left["LS"], right_membership["ZA"])
        rules_outputs_right["LS"] = max(rules_outputs_right["LS"], right_membership["ZA"])

    if left_membership["SD"] and right_membership["PSA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PSA"])
        rules_outputs_right["AS"] = max(rules_outputs_right["AS"], right_membership["PSA"])
    
    if left_membership["SD"] and right_membership["PAA"] > 0:
        rules_outputs_left["BS"] = max(rules_outputs_left["BS"], right_membership["PAA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["PAA"])
    
    if left_membership["SD"] and right_membership["PBA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["PBA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["PBA"])

####if AD AND PBA,PAA,PSA,ZA,NSA,NAA,NBA RULES VR,VL
    if left_membership["AD"] and right_membership["NBA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NBA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NBA"])

    if left_membership["AD"] and right_membership["NAA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NAA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NAA"])

    if left_membership["AD"] and right_membership["NSA"] > 0:
        rules_outputs_left["BS"] = max(rules_outputs_left["BS"], right_membership["NSA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NSA"])

    if left_membership["AD"] and right_membership["ZA"] > 0:
        rules_outputs_left["AS"] = max(rules_outputs_left["AS"], right_membership["ZA"])
        rules_outputs_right["AS"] = max(rules_outputs_right["AS"], right_membership["ZA"])

    if left_membership["AD"] and right_membership["PSA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PSA"])
        rules_outputs_right["BS"] = max(rules_outputs_right["BS"], right_membership["PSA"])
    
    if left_membership["AD"] and right_membership["PAA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PAA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PAA"])
    
    if left_membership["AD"] and right_membership["PBA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PBA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PBA"])

    

####if BD AND PBA,PAA,PSA,ZA,NSA,NAA,NBA RULES VR,VL
    if left_membership["BD"] and right_membership["NBA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NBA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NBA"])

    if left_membership["BD"] and right_membership["NAA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NAA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NAA"])

    if left_membership["BD"] and right_membership["NSA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NSA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NSA"])

    if left_membership["BD"] and right_membership["ZA"] > 0:
        rules_outputs_left["BS"] = max(rules_outputs_left["BS"], right_membership["ZA"])
        rules_outputs_right["BS"] = max(rules_outputs_right["BS"], right_membership["ZA"])

    if left_membership["BD"] and right_membership["PSA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PSA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PSA"])
    
    if left_membership["BD"] and right_membership["PAA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PAA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PAA"])

    if left_membership["BD"] and right_membership["PBA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PBA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PBA"])
    
    
        
####if VBD AND PBA,PAA,PSA,ZA,NSA,NAA,NBA RULES VR,VL
    if left_membership["VBD"] and right_membership["NBA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NBA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NBA"])
    
    if left_membership["VBD"] and right_membership["NAA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NAA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NAA"])

    if left_membership["VBD"] and right_membership["NSA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["NSA"])
        rules_outputs_right["VLS"] = max(rules_outputs_right["VLS"], right_membership["NSA"])

    if left_membership["VBD"] and right_membership["ZA"] > 0:
        rules_outputs_left["VBS"] = max(rules_outputs_left["VBS"], right_membership["ZA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["ZA"])

    if left_membership["VBD"] and right_membership["PSA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PSA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PSA"])

    if left_membership["VBD"] and right_membership["PAA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PAA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PAA"])
        
    if left_membership["VBD"] and right_membership["PBA"] > 0:
        rules_outputs_left["VLS"] = max(rules_outputs_left["VLS"], right_membership["PBA"])
        rules_outputs_right["VBS"] = max(rules_outputs_right["VBS"], right_membership["PBA"])
    
    

    # Дефазифікація
    left_pwm = defuzzification(rules_outputs_left)
    right_pwm = defuzzification(rules_outputs_right)

    # Виведення PWM значень
    print("Left PWM after defuzzification:", left_pwm)
    print("Right PWM after defuzzification:", right_pwm)

    return left_pwm, right_pwm