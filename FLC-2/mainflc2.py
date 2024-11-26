import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from fuzzy_logic import fuzzy_logic, pwm_to_speed
from graph import plot_data, initialize_file, log_data, diagraam
import math  

# запуск симуляції
client = RemoteAPIClient()
sim = client.require('sim')

sim.setStepping(True)
sim.startSimulation()

motorLeft = sim.getObject("/PioneerP3DX/leftMotor")
motorRight = sim.getObject("/PioneerP3DX/rightMotor")
last_log_time = time.time()
# файл для запису 
filename = "robot_data.txt"
initialize_file(filename)

# Основний цикл
try:
    while True:
        coordinates = sim.getObjectPosition(sim.getObject("/PioneerP3DX"), -1)[:2]
        # інформація з датчиків
        left_sensor_value = sim.readProximitySensor(sim.getObject("/PioneerP3DX/ultrasonicSensor[2]"))[1]
        right_sensor_value = sim.readProximitySensor(sim.getObject("/PioneerP3DX/ultrasonicSensor[5]"))[1]
        time.sleep(0.0010)
        print(f"Left Sensor Value: {left_sensor_value:.2f} m, Right Sensor Value: {right_sensor_value:.2f} m")
        # Передавання входів датчиків у бібліотеку нечіткої логіки
        left_pwm, right_pwm = fuzzy_logic(left_sensor_value, right_sensor_value)
        # PWM на мотори
        sim.setJointTargetVelocity(motorLeft, pwm_to_speed(left_pwm))
        sim.setJointTargetVelocity(motorRight, pwm_to_speed(right_pwm))

        # Запис файлу
        current_time = sim.getSimulationTime()
        pos = sim.getObjectPosition(motorLeft, -1)
        left_speed = pwm_to_speed(left_pwm) 
        right_speed = pwm_to_speed(right_pwm) 
        if time.time() - last_log_time >= 1:  # кожну секунду
            log_data(filename, f"{int(current_time)},{coordinates[0]:.5f},{coordinates[1]:.5f},{left_sensor_value:.5f},{left_sensor_value:.5f}, {int(left_pwm)},{int(right_pwm)},{(left_speed * 0.1):.5f},{(right_speed * 0.1):.5f}\n")
            last_log_time = time.time()  # оновлюємо час останнього запису

        # Крок симуляції
        
        sim.step()
        #time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    sim.stopSimulation()
    print("Simulation stopped.")

# виклик графіку
plot_data(filename)
diagraam()