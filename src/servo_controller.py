import time
import logging
from pca9685 import PCA9685
import time


class ServoController():

    def __init__(self):
        """Set up the servos"""
        logging.info('Setting up servo')
        self._set_servo_range()
        self.pca_controller = PCA9685(1, 0x40, 7)
        self.pca_controller.set_frequency(50)
        self.pca_controller.set_sleep(False)

    def _set_servo_range(self):
        """Sets the range of the servo"""
        self.servo_bounds_degrees = 20
        self.servo_max = 180 - self.servo_bounds_degrees
        self.servo_min = self.servo_bounds_degrees
        self.servo_range = self.servo_max - self.servo_min

    def __del__(self):
        """Clean up"""
        self.pca_controller.set_sleep(True)

    def set_servo_angle(self, angle):
        """Set the angle of the servo"""
        logging.info('Setting angle to {}'.format(angle))
        # Period 20ms
        # 0.5ms (2.5% duty cycle) = 0 deg
        # 2.5ms (12.5% duty cycle) = 180 deg
        self.pca_controller.set_duty(1, (angle * 10 / 180 + 2.5)/100)

    def set_servo_percent(self, percent):
        """Converts a decimal percentage into servo angle"""
        angle = int((1 - percent) * self.servo_range) + self.servo_min
        self.set_servo_angle(angle)
