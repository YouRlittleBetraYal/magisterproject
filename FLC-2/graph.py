import numpy as np
import matplotlib.pyplot as plt
import os

def log_data(filename, data):
    """Запис даних у файл."""
    with open(filename, "a") as output_file:
        output_file.write(data)

def initialize_file(filename):
    """Ініціалізація файлу з заголовками або очищення існуючого."""
    if os.path.exists(filename):
        # Якщо файл існує, очищаємо його
        open(filename, "w").close()
    else:
        # Якщо файл не існує, створюємо новий
        with open(filename, "w") as output_file:
            output_file.write("Time,Robot X,Y,d - target,fi - angle,Object X,Y, Pwm -left, Pwm - right, Left_Speed(mm/s),Right_Speed(mm/s)\n")

def plot_data(filename):
    """Візуалізація даних з файлу."""
    data = np.loadtxt(filename, delimiter=',', skiprows=1)
    x_data = data[:, 1]
    y_data = data[:, 2]

    # Візуалізація
    plt.figure(figsize=(10, 6))
    plt.plot(x_data, y_data, label='Траекторія', marker='o', markersize=2)

    # Додавання легенди
    plt.title("Траекторія робота до цілі (X:-1.70000, Y:1.70000)")
    plt.xlabel("X Position (m)")
    plt.ylabel("Y Position (m)")
    plt.legend(loc='upper right')
    plt.grid()

    # Додавання текстової інформаці

    plt.show()
    
def diagraam():
    # Відкриваємо файл та зчитуємо дані
    data = np.loadtxt('robot_data.txt', delimiter=',', skiprows=1)
    # Розділяємо дані
    time = data[:, 0]
    left_speed = data[:, 7] *1000
    right_speed = data[:, 8] *1000

    # 3. Зміна швидкостей VR та VL під час руху МРП
    plt.figure()
    plt.plot(time, right_speed, label='VR - швидкість правого колеса (мм/с)')
    plt.plot(time, left_speed, label='VL - швидкість лівого колеса (мм/с)')
    plt.xlabel('Час (s)')
    plt.ylabel('Швидкість (мм/с)')
    plt.title(f'Зміна швидкостей VR та VL ')
    plt.grid(True)
    plt.legend()
    plt.show()
