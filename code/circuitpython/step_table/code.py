#
# Calculates the PWM output for 3 bipolar coils using a lookup table of values
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

DIRECTION_FORWARDS = 1
DIRECTION_BACKWARDS = -1

# PWM output steps for the 3 coil phases
# Each of these values are from -100 to +100
STEPS = [
  [25, 0, -75 ],
  [50, 0, -50 ],
  [75, 0, -25 ],
  [100, 0, 0 ],
  [75, 25, 0 ],
  [50, 50, 0 ],
  [25, 75, 0 ],
  [0, 100, 0 ],
  [0,  75, 25 ],
  [0, 50, 50 ],
  [0,  25, 75 ],
  [0,  0, 100 ],
  [-25,  0, 75 ],
  [-50, 0, 50 ],
  [-75, 0, 25 ],
  [-100, 0, 0 ],
  [-75, -25, 0 ],
  [-50, -50, 0 ],
  [-25,  -75, 0 ],
  [0, -100, 0 ],
  [0, -75, -25, ],
  [0, -50, -50 ],
  [0, -25, -75 ],
  [0, 0, -100 ],
]
NUM_STEPS = len(STEPS)

class LinearActuator:
    def __init__(self):
        self.running = 1
        self.current_step = 1
        self.last_step = -1
        self.step_increment = .1 # If the value is 0.1, each step will be divided into 10 steps
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
        multiplier = (value / 100)
        if value >= 0:
            # Positive current flow
            low_pwm.duty_cycle = 0
            time.sleep(DEAD_TIME)
            high_pwm.duty_cycle = int(multiplier * PWM_MAX)
        else:
            # Negative current flow
            high_pwm.duty_cycle = 0
            time.sleep(DEAD_TIME)
            low_pwm.duty_cycle = int(-1 * multiplier * PWM_MAX)

    def normalize_step(self, idx):
      """Wrap the step index around, if necessary"""
      if idx >= NUM_STEPS:
          idx -= NUM_STEPS
      elif idx < 0:
          idx += NUM_STEPS
      return idx

    def interpolate_value(self, from_value, to_value, percent):
      """Return a value that is between from_value and to_value by a percentage between 0.0 and 1.0"""
      if from_value == to_value:
        return to_value
      if percent <= 0:
        return from_value
      if percent >= 1:
        return to_value
      diff = to_value - from_value
      return (percent * diff) + from_value

    def step(self):
        """Update all output phases"""
        if not self.running:
            self.output_off()
            return

        # Increment current step
        self.last_step = self.current_step
        if self.direction == DIRECTION_FORWARDS:
            self.current_step += self.step_increment
        else:
            self.current_step -= self.step_increment
        self.current_step = self.normalize_step(self.current_step)

        # Get the percent progress we've made to the next step in the list
        progress = 0
        from_idx = int(self.current_step)
        to_idx = int(self.current_step)
        if self.direction == DIRECTION_FORWARDS:
          from_idx = math.floor(self.current_step)
          to_idx = math.ceil(self.current_step)
          progress = 1 - (to_idx - self.current_step)
        else:
          from_idx = math.ceil(self.current_step)
          to_idx = math.floor(self.current_step)
          progress = 1 - (self.current_step - to_idx)

        # Calculate the phase values
        to_idx = self.normalize_step(to_idx)
        from_idx = self.normalize_step(from_idx)
        (from_a, from_b, from_c) = STEPS[from_idx]
        (to_a, to_b, to_c) = STEPS[to_idx]

        phase_a = self.interpolate_value(from_a, to_a, progress)
        phase_b = self.interpolate_value(from_b, to_b, progress)
        phase_c = self.interpolate_value(from_c, to_c, progress)

        # Only print full step changes
        if int(self.last_step) != int(self.current_step):
            print("Step %i (%i, %i, %i)" % (self.current_step, phase_a, phase_b, phase_c))

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

if __name__ == "__main__":
    actuator = LinearActuator()
    actuator.direction = DIRECTION_FORWARDS
    steps = 0
    target_cycle =  round(NUM_STEPS * (actuator.step_increment * 100)) * 2
    try:
        actuator.start()
        while True:
            actuator.step()
            steps += 1
            if steps % target_cycle == 0:
                actuator.direction *= -1

            # Small delay to control update rate
            time.sleep(0.001)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        actuator.stop()

