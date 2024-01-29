import argparse
import datetime
import math
import random
import time
import matplotlib.pyplot as plt

def cpu_workload_simulation(amplitude, frequency, duration, step_size, spike_probability, spike_amplitude):
    start_time = time.time()
    end_time = start_time + duration * 3600  # Convert duration from hours to seconds

    time_values = []
    workload_values = []

    current_time = 0  # Initialize current time

    while current_time < duration * 100:
        # Simulate the regular workload
        workload = amplitude * math.sin(2 * math.pi * frequency * current_time)
        workload = abs(workload)

        # Introduce spikes randomly based on the given probability
        if random.random() < spike_probability:
            workload += spike_amplitude

        result = math.sqrt(workload)
        time_values.append(current_time)
        workload_values.append(workload)
        current_time += step_size

    # Plot the CPU workload
    plt.plot(time_values, workload_values)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Workload')
    plt.title('CPU Workload Simulation with Spikes')
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simulate CPU workload over time.")
    parser.add_argument('--amplitude', type=float, default=10.0, help="Amplitude of the workload")
    parser.add_argument('--frequency', type=float, default=0.1, help="Frequency of the workload (in Hz)")
    parser.add_argument('--duration', type=float, default=1.0, help="Duration of the simulation (in hours)")
    parser.add_argument('--step_size', type=float, default=1.0, help="Simulation step size (in seconds)")
    parser.add_argument('--spike_probability', type=float, default=0.05, help="Probability of a spike occurring at each step")
    parser.add_argument('--spike_amplitude', type=float, default=20.0, help="Amplitude of the spike")
    args = parser.parse_args()

    cpu_workload_simulation(args.amplitude, args.frequency, args.duration, args.step_size, args.spike_probability, args.spike_amplitude)