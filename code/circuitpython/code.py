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
PHASE_ANGLE = 2 * math.pi / 3.0  # 120 degrees of each other

class LinearActuator:
    def __init__(self):
        self.angle = 0.0
        self.direction = True
        self.step_increment = .05 # How much to move, in radians, with each step
        self.running = 1
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
        if direction > 0:
            self.angle += self.step_increment
        else:
            self.angle -= self.step_increment

        # Keep angle in range 0-2π
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi
        elif self.angle < 0:
            self.angle += 2 * math.pi

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

        degrees = math.degrees(self.angle)
        print("Angle: %f, Degrees: %s" % (self.angle, degrees))

        # Calculate phase values
        phase_a = math.cos(self.angle)
        phase_b = math.cos(self.angle - PHASE_ANGLE)
        phase_c = math.cos(self.angle + PHASE_ANGLE)

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
        full_cycle =(2 * math.pi) / actuator.step_increment
        target_cycle =  round(full_cycle * 2)

        while True:
            actuator.step(direction)
            actuator.update()
            steps += 1

            if steps % target_cycle == 0:
                direction *= -1

            # Small delay to control update rate
            time.sleep(.01)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        actuator.stop()
