import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from fuzzy_logic_flc1 import fuzzy_logic, pwm_to_speed, calculate_distance, calculate_angle
from graph import plot_data, initialize_file, log_data,diagraam
import math  

# запуск симуляції Copeliasim
client = RemoteAPIClient()
sim = client.require('sim')
sim.setStepping(True)
sim.startSimulation()
#отримання об'єктів лівого/правого двигуна
motorLeft = sim.getObject("/PioneerP3DX/leftMotor")
motorRight = sim.getObject("/PioneerP3DX/rightMotor")
#таймер
last_log_time = time.time()
last_log_simulation_time = 0  # Спочатку 0 для негайного запису
# файл для запису даних
filename = "robot_data.txt"
initialize_file(filename)

# Основний цикл
try:
    while True:
        # отримуємо координати робота
        left_sensor_position = sim.getObjectPosition(sim.getObject("/PioneerP3DX"), -1)[:2]  # Координати робота (x, y)
        # отримуємо координати об'єкта (квітки)
        right_sensor_position = sim.getObjectPosition(sim.getObject("/indoorPlant"), -1)[:2] 
        orientation = sim.getObjectOrientation(sim.getObject("/PioneerP3DX"), -1)  # Отримуємо початкову орієнтацію
        robot_orientation = orientation[2]
        robot_orientation_deg = robot_orientation * (180 / math.pi)
        # викликаємо функціїю обчислення відстані та кута до цілі (кітки)
        distance_to_target = calculate_distance(left_sensor_position, right_sensor_position)
        angle_to_target = calculate_angle(left_sensor_position, right_sensor_position,robot_orientation_deg)
        print(f"distance to target:", distance_to_target)
        
        time.sleep(0.0010)
        
        print(f"Left Sensor Value (Robot Position): x = {left_sensor_position[0]:.2f} m, y = {left_sensor_position[1]:.2f} m")
        print(f"Right Sensor Value (Target Position): x = {right_sensor_position[0]:.2f} m, y = {right_sensor_position[1]:.2f} m")
        print(f"Angle to Target: {angle_to_target:.2f} degrees", end='\r')  # Доданий вивід кута
       
        # Передавання входів датчиків у бібліотеку нечіткої логіки
        left_pwm, right_pwm = fuzzy_logic(distance_to_target, angle_to_target)

        # PWM на мотори
        sim.setJointTargetVelocity(motorLeft, pwm_to_speed(left_pwm))
        sim.setJointTargetVelocity(motorRight, pwm_to_speed(right_pwm))

        # Запис файлу
        current_simulation_time = sim.getSimulationTime()
        pos = sim.getObjectPosition(motorLeft, -1)
        left_speed = pwm_to_speed(left_pwm) 
        right_speed = pwm_to_speed(right_pwm)
        
        if current_simulation_time - last_log_simulation_time >= 1:
            log_data(filename, f"{int(current_simulation_time)},{left_sensor_position[0]:.5f},{left_sensor_position[1]:.5f},{distance_to_target:.5f},{angle_to_target},{right_sensor_position[0]:.5f},{right_sensor_position[1]:.5f},{int(left_pwm)},{int(right_pwm)},{(left_speed * 0.1):.5f},{(right_speed * 0.1):.5f}\n")
            last_log_simulation_time = current_simulation_time

        # Крок симуляції
        sim.step()
        #time.sleep(0.07)
except KeyboardInterrupt:
    pass
finally:
    sim.stopSimulation()
    print("Simulation stopped.")

# виклик графіку
plot_data(filename)
diagraam()
