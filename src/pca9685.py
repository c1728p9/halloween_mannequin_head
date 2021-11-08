import smbus
import RPi.GPIO as gpio

class PCA9685:
    REG_MODE1 = 0x00
    REG_MODE2 = 0x01
    REG_PRE_SCALE = 0xFE
    REG_PWM_BASE = 0x06
    MODE1_INIT = 0x30 # Sleep on, Auto increment on
    MODE2_INIT = 0x04
    PERIOD = 4096
    PWM_CHANNELS = 16
    PRESCALE_MIN = 0x03
    PRESCALE_MAX = 0xFF
    
    def __init__(self, channel, address=0x40, enable_pin=7):
        self.bus = smbus.SMBus(channel)
        self.address = address
        self.enable_pin = enable_pin
        self.sleeping = True
        
        # Initialize chip
        self.bus.write_i2c_block_data(self.address, self.REG_MODE1, [self.MODE1_INIT])
        self.bus.write_i2c_block_data(self.address, self.REG_MODE2, [self.MODE2_INIT])
        for i in range(self.PWM_CHANNELS):
            self.set_duty_raw_4096(i, 0)

        gpio.setmode(gpio.BOARD)
        gpio.setup(self.enable_pin, gpio.OUT)
        gpio.output(self.enable_pin, False)
    
    def reset(self):
        self.bus.write_i2c_block_data(0, 6, [])
        
    def set_duty(self, channel, duty):
        if duty < 0 or duty > 1:
            raise Exception("Duty cycle of %s is outside allowed range of 0.0 to 1.0"  % duty)
        on_cycles = int(round(self.PERIOD * duty))
        self.set_duty_raw_4096(channel, on_cycles)

    def set_duty_raw_4096(self, channel, on_cycles):
        """Set the number of on cycles within a 4096 cycle window
        
        Note:
        0 cycles - off (no PWM)
        4095 cycles - max duty cycle
        """
        if channel < 0 or channel > self.PWM_CHANNELS:
            raise Exception("PWM channel of %s is outside allowed range of 0 to %s"  % (channel, self.PWM_CHANNELS))
        if on_cycles >= self.PERIOD:
            # Note - 100% duty cycle not possible
            on_cycles = self.PERIOD - 1
        values = [
            0, # on low
            0, # on high
            ((on_cycles >> 0) & 0xFF),# off low
            ((on_cycles >> 8) & 0xFF),# off high
        ]
        self.bus.write_i2c_block_data(self.address, self.REG_PWM_BASE + channel * 4, values)

        
    def set_frequency(self, frequency):
        prescale = int(round(25000000/4096/frequency)) - 1
        self.set_prescaler_raw(prescale)

    
    def set_prescaler_raw(self, prescale_value):
        # Frequency = 25MHz / 4096 / (prescale + 1)
        # Ex. prescale of 0x03h is 1526Hz
        # Ex. prescale of 0xFF is 24Hz
    
        if not self.sleeping:
            raise Exception("Prescaler can only be changed in sleep mode")

        if prescale_value < self.PRESCALE_MIN or prescale_value > self.PRESCALE_MAX:
            raise Exception("Prescale of %s is outside allowed range of %s to %s"  % (prescale_value, self.PRESCALE_MIN, self.PRESCALE_MAX))

        self.bus.write_i2c_block_data(self.address, self.REG_PRE_SCALE, [prescale_value])

    def set_sleep(self, sleep):
        value = ((1 if sleep else 0) << 4) | (1 << 5)
        self.bus.write_i2c_block_data(self.address, self.REG_MODE1, [value])
        self.sleeping = sleep
        
    def reset_all_raw(self):
        """Reset all PCA9685 devices on the I2C bus"""
        self.bus.write_i2c_block_data(0, 6, [])
