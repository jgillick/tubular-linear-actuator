#
# Calculates the PWM output for 3 bipolar coils using a sine wave.
#
import board
import pwmio
import digitalio
import time
import math

# PWM setup for each phase - both high and low side
# Adjust pins according to your board
pwm_ah = pwmio.PWMOut(board.D5, frequency=20000, duty_cycle=0)
pwm_al = pwmio.PWMOut(board.D6, frequency=20000, duty_cycle=0)
pwm_bh = pwmio.PWMOut(board.D9, frequency=20000, duty_cycle=0)
pwm_bl = pwmio.PWMOut(board.D10, frequency=20000, duty_cycle=0)
pwm_ch = pwmio.PWMOut(board.D11, frequency=20000, duty_cycle=0)
pwm_cl = pwmio.PWMOut(board.D12, frequency=20000, duty_cycle=0)

# Constants
PWM_MAX = 65535  # 16-bit PWM
DEAD_TIME = 0.000001  # 1 microsecond dead time
PHASE_OFFSET = 2 * math.pi / 3.0  # 120 degrees of each other
DEGREE_TO_RADIAN_MULTIPLIER = math.pi / 180

DIRECTION_FORWARDS = 1
DIRECTION_BACKWARDS = -1

class LinearActuator:
    def __init__(self):
        self.running = 1
        self.degrees = 0.0 # Current position, in degrees of a full cycle (0 - 360)
        self.step_increment =  .5 # How many degrees to increment at each step
        self.direction = DIRECTION_FORWARDS
        self.output_off()

    def output_off(self):
        """Turn off all output"""
        pwm_ah.duty_cycle = 0
        pwm_al.duty_cycle = 0
        pwm_bh.duty_cycle = 0
        pwm_bl.duty_cycle = 0
        pwm_ch.duty_cycle = 0
        pwm_cl.duty_cycle = 0

    def apply_phase(self, high_pwm, low_pwm, value):
        """Apply PWM to one phase with dead time"""
        if value >= 0:
            # Positive current flow
            low_pwm.duty_cycle = 0
            time.sleep(DEAD_TIME)
            high_pwm.duty_cycle = int(value * PWM_MAX)
        else:
            # Negative current flow
            high_pwm.duty_cycle = 0
            time.sleep(DEAD_TIME)
            low_pwm.duty_cycle = int(-value * PWM_MAX)

    def step(self, direction):
        """ Adjust angle to step in one direction or the other. (direction: 1 or -1)"""
        if direction == DIRECTION_FORWARDS:
            self.degrees += self.step_increment
        else:
            self.degrees -= self.step_increment

        # Keep angle in range of one cycle (360 degrees)
        if self.degrees >= 360:
            self.degrees -= 360
        elif self.degrees < 0:
            self.degrees += 360

    def next_step(self):
        """Set the next step angle"""
        self.step(1)

    def previous_step(self):
        """Set the next step angle"""
        self.step(-1)

    def update(self):
        """Update all output phases"""
        if not self.running:
            self.output_off()
            return

        print("Degrees: %f" % (self.degrees))

        # Calculate phase values
        radians = self.degrees * DEGREE_TO_RADIAN_MULTIPLIER
        phase_a = math.cos(radians)
        phase_b = math.cos(radians - PHASE_OFFSET)
        phase_c = math.cos(radians + PHASE_OFFSET)

        # Apply to H-bridges
        self.apply_phase(pwm_ah, pwm_al, phase_a)
        self.apply_phase(pwm_bh, pwm_bl, phase_b)
        self.apply_phase(pwm_ch, pwm_cl, phase_c)


    def start(self):
        """Start the actuator"""
        self.running = True

    def stop(self):
        """Stop the actuator"""
        self.running = False
        self.output_off()

# Example usage
if __name__ == "__main__":
    actuator = LinearActuator()
    direction = 1
    steps = 0
    try:
        actuator.start()
        actuator.update()
        full_cycle = 360 / actuator.step_increment
        target_cycle =  round(full_cycle * 1.5)

        while True:
            actuator.step(direction)
            actuator.update()
            steps += 1

            if steps % target_cycle == 0:
                direction *= -1

            # Small delay to control update rate
            time.sleep(.0001)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        actuator.stop()
