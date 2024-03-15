#Nytt skelett till Target Service
from __future__ import annotations
from flask import Flask,request
from flask_restful import Api, Resource
import requests
import threading
import sys
import math
from datetime import datetime, timedelta
import itertools
import random
from collections import deque
from enum import Enum
from typing import Generator, Callable
from matplotlib import pyplot as plt

from scaling_time_options import ScalingTimeOptions
from service_instance_state import ServiceInstanceState
from target_service_instance import TargetServiceInstance
import json
import pandas as pd

app = Flask(__name__)
api = Api(app)
LoadGenBASE = "http://127.0.0.1:8009/"
LoadRecBASE = "http://127.0.0.1:8008/"
PredictorBASE = "http://127.0.0.1:8010/"

SCALING_THRESHOLD = 0.2
SCALE_UP_TIME = ScalingTimeOptions(mean_time=timedelta(hours=1), std_dev=timedelta(hours=0.01))
SCALE_DOWN_TIME = ScalingTimeOptions(mean_time=timedelta(hours=1), std_dev=timedelta(hours=0.01))

class TargetService(Resource):

    def __init__(
            self, 
            applied_load: 0, 
            current_time: datetime,
            scale_up_time: ScalingTimeOptions,
            scale_down_time: ScalingTimeOptions,
            starting_instances: int = 0,
            ready_instances: int = 0,
            instance_load: float = 20000,
            instance_baseline_load: float = 10,
            starting_load: float = 20000,
            terminating_load: float = 20000
    ):
        self.current_time: datetime = current_time
        self.applied_load: float = applied_load
        self.scale_up_time: ScalingTimeOptions = scale_up_time
        self.scale_down_time: ScalingTimeOptions = scale_down_time
        self.instance_load_capability: float = instance_load
        self.instance_baseline_load: float = instance_baseline_load
        self.starting_load: float = starting_load
        self.terminating_load: float = terminating_load
        self.experienced_load: float = 0
        self.processed_load: float = 0

        starting = [
            TargetServiceInstance.start_new(
                current_time,
                scale_up_time,
                self.instance_load_capability
            )
            for _ in range(starting_instances)
        ]

        ready = [
            TargetServiceInstance(
                current_time=current_time,
                started_time=current_time,
                ready_time=current_time,
                handled_load=self.instance_load_capability
            )
            for _ in range(ready_instances)
        ]

        self.instances: deque[TargetServiceInstance] = deque(starting + ready)
        self.counts: dict[ServiceInstanceState, int] = {
            state: self.count(state)
            for state in ServiceInstanceState
        }

        self.total_load_capability: float = sum(
            instance.load_capability \
            for instance in self.instances \
            if instance.state == ServiceInstanceState.READY
        )
    def count(self, state: ServiceInstanceState):
        """
        Counts the current number of services of a specified state.
        :param state: The state to count service instances of.
        :return: The number of instances of the service with the specified state.
        """
        return sum(1 for instance in self.instances if instance.state == state)

    def get_victims(
            self,
            count: int
    ) -> Generator[TargetServiceInstance, None, None]:
        """
        Get the most viable instances to be terminated. Starts off by terminating
        starting instances in order of start time, i.e. newest instances are
        returned first. Then, ready (running) instances are returned in the same
        order, where younger instances are returned first.
        :param count: The number of instances to return
        :return: A generator yielding the victim instances in the mentioned order.
        """
        starting = sorted(
            filter(
                lambda instance: instance.state == ServiceInstanceState.STARTING,
                self.instances
            ),
            key=lambda instance: instance.started_time
        )

        running = sorted(
            filter(
                lambda instance: instance.state == ServiceInstanceState.READY,
                self.instances
            ),
            key=lambda instance: instance.ready_time
        )

        yield from itertools.islice(
            itertools.chain(
                starting,
                running
            ),
            count
        )

    def cleanup(self):
        """
        Remove instances in the OFF state from the instance list.
        :return:
        """
        off_instances = list(filter(
            lambda instance: instance.state == ServiceInstanceState.OFF,
            self.instances
        ))

        for off_instance in off_instances:
            self.instances.remove(off_instance)

    def _calculate_experienced_load(self):
        """
        Get the total and processed loads.
        :return: A tuple of the total load, and the processed load. The total load is
        the resource utilization of the system, while the processed load is how much
        of the applied load the system is able to process.
        """
        constant_loads = {
            ServiceInstanceState.STARTING: self.starting_load,
            ServiceInstanceState.READY: self.instance_baseline_load,
            ServiceInstanceState.TERMINATING: self.terminating_load
        }

        total_load = 0.
        total_load_capability = 0

        for instance in self.instances:
            constant_load = constant_loads.get(instance.state)
            if constant_load is None:
                constant_load = 0

            total_load += constant_load

            if instance.state == ServiceInstanceState.READY:
                total_load_capability += instance.load_capability - constant_load

        # We cant process more load than we have capability for. Therefore, disregard
        # any applied load exceeding the current processing capability
        processed_load = min(self.applied_load, total_load_capability)
        total_load += processed_load

        return total_load, processed_load, total_load_capability

    def update(self, current_time: datetime, applied_load: float,
               delta_instances: int | Callable[[TargetService], int]):
        """
        Updates the instances of the service with the current time, and scales the
        system if necessary.
        :param current_time: The current simulated time.
        :param applied_load: The current load applied to the system.
        :param delta_instances: The number of instances to add/remove, or a function
        receiving this class instance that returns the number of instances to
        add/remove. A negative number means that instances are removed, i.e. the
        system is scaled down. A positive number instead scales the system up. Note
        that it takes time to scale the system, this parameter only initiates the
        desired scaling.
        :return:
        """
        self.current_time = current_time
        self.applied_load = applied_load

        # Update all running instances with the current time
        for instance in self.instances:
            instance.update(current_time)

        # Calculate the experienced and processed loads
        self.experienced_load, self.processed_load, self.total_load_capability = \
            self._calculate_experienced_load()

        if not isinstance(delta_instances, int):
            delta_instances = delta_instances(self)

        # If we need to scale down, find some victims and terminate them
        if delta_instances < 0:
            victims = self.get_victims(abs(delta_instances))

            for victim in victims:
                victim.terminate(self.scale_down_time)
        elif delta_instances > 0:
            # If we need to scale up, add some new instances
            self.instances.appendleft(TargetServiceInstance.start_new(
                current_time=current_time,
                handled_load=self.instance_load_capability,
                options=self.scale_up_time
            ))

        # Update the state of all running instances to reflect the current time
        for state in ServiceInstanceState:
            self.counts[state] = self.count(state)

        # Remove instances in the OFF state
        self.cleanup()
         

def start_flask():
    app.run(debug=False, port=8003,use_reloader=False, host='0.0.0.0') #Startar flask server för TargetService på en annan tråd! 

def calculate_instances(
        service: TargetService
) -> int:
    processed_load = service.processed_load
    process_capability = service.total_load_capability

    process_utilization = 0 if processed_load == 0 else \
        processed_load / process_capability

    desired_mean_load = 0.5
    upper_threshold = desired_mean_load + SCALING_THRESHOLD
    lower_threshold = desired_mean_load - SCALING_THRESHOLD

    if lower_threshold < process_utilization < upper_threshold:
        return 0

    scaling_factor = process_utilization / desired_mean_load
    current_instances = service.count(ServiceInstanceState.READY)
    starting_instances = service.count(ServiceInstanceState.STARTING)
    terminating_instances = service.count(ServiceInstanceState.TERMINATING)

    down_instances = math.ceil(
        (current_instances - terminating_instances) * scaling_factor
    )

    up_instances = math.ceil(
        (current_instances + starting_instances) * scaling_factor
    )

    if scaling_factor > 1:
        return up_instances
    elif current_instances - down_instances > 0:
        return -down_instances

    return 0


def simulate_run():
    response = requests.get(
    LoadGenBASE + "load_generator",
    params={"start_date": start_date,"end_date":end_date, "resample_frequency": resample_frequency}
)
    requests.post(PredictorBASE + "predict", 
                      json={"start_date": start_date,
                            "end_date": end_date}
                            )
    response_data = response.json()
    parsed_data = json.loads(response_data)
    try:
        df_hourly = pd.DataFrame(parsed_data)  # Convert JSON data to DataFrame
        df_hourly['time'] = pd.to_datetime(df_hourly['time'], unit='ms')
        df_hourly = df_hourly.resample('H', on='time').sum()
        df_hourly = df_hourly.reset_index()
        df_hourly['method_count'] = df_hourly['method_count'].astype(float)
        print("Received DataFrame:")
        print(df_hourly.head())
        print(df_hourly.tail())
    except ValueError as e:
        print("Error:", e)
        
    # High load for a minute every 5 minutes
    per_hour_loads = df_hourly["method_count"]

    current_time = df_hourly['time'].iloc[0]
    step = timedelta(hours=1)

    service = TargetService(
        current_time=current_time,
        applied_load=per_hour_loads[0],
        scale_up_time=SCALE_UP_TIME,
        scale_down_time=SCALE_DOWN_TIME,
        ready_instances=4
    )

    experienced_loads = []
    ready_instances = []
    instances = []

    for load in per_hour_loads:
        current_time += step
        service.update(
            current_time=current_time,
            applied_load=load,
            delta_instances=calculate_instances
        )

        experienced_loads.append(service.experienced_load)
        ready_instances.append(service.count(ServiceInstanceState.READY))
        instances.append(len(service.instances))
        requests.post(LoadRecBASE + "loadrecorder",
                      json={"applied_load": service.applied_load, 
                            "experienced_load": service.experienced_load,
                            "current_time": str(service.current_time),
                            "instances": len(service.instances)})

    hours = [
        i
        for i in range(len(df_hourly))
    ]

    return hours, per_hour_loads, experienced_loads, instances, ready_instances

def plot_loads(
        hours: list[int],
        applied_loads: list[float],
        experienced_loads: list[float],
        total_instances: list[int],
        ready_instances: list[int]
):
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    lines = []
    lines.extend(ax2.plot(hours, ready_instances, '-', label='Ready instances'))
    # lines.extend(ax2.plot(minutes, total_instances, label='Total instances'))
    lines.extend(ax.plot(hours, experienced_loads, '-r', label='Experienced load'))
    lines.extend(ax.plot(hours, applied_loads, '-g', label='Applied load'))

    ax.set(xlabel='Time (hours)', ylabel='Load', title='System load')
    ax2.set(ylabel='Instances')
    ax.grid()
    ax.legend(lines, [line.get_label() for line in lines], loc=0)
    ax2.set_ylabel('Instances')
    plt.show()

def main():
    args = simulate_run()
    plot_loads(*args)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python targetservice.py start_date end_date resample_frequency")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    resample_frequency = sys.argv[3]


    flask_thread = threading.Thread(target=start_flask) #Flaskservern måste köras på en egen tråd! annars kan man inte köra annan kod samtidigt 
    flask_thread.start()

    main()
    
    


