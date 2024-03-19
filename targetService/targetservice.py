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
SCALE_UP_TIME = ScalingTimeOptions(mean_time=timedelta(hours=2), std_dev=timedelta(hours=0.01))
SCALE_DOWN_TIME = ScalingTimeOptions(mean_time=timedelta(hours=2), std_dev=timedelta(hours=0.01))

class TargetService(Resource):

    def __init__(
            self, 
            applied_load: 0, 
            current_time: datetime,
            scale_up_time: ScalingTimeOptions,
            scale_down_time: ScalingTimeOptions,
            starting_instances: int = 0,
            ready_instances: int = 0,
            instance_load: float = 1000,
            instance_baseline_load: float = 1,
            starting_load: float = 1000,
            terminating_load: float = 1000,
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

def add_future_knowledge(current_load, future_load):
    if future_load > current_load:
        delta_instances = calculate_instances(current_load, future_load)
    elif future_load < current_load:
        delta_instances = calculate_instances(current_load, future_load)
    else:
        delta_instances = 0 

    return delta_instances

def calculate_instances(
        service: TargetService, future_load: float
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
    scaling_factor_future = future_load / desired_mean_load if future_load is not None else None

    if scaling_factor_future is not None:
        if scaling_factor_future > 1 and scaling_factor > 1:
            scaling_factor = max(scaling_factor, scaling_factor_future)
        elif scaling_factor_future < 1 and scaling_factor < 1:
            scaling_factor = min(scaling_factor, scaling_factor_future)

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

def remove_outliers(df):
        Q1 = df['method_count'].quantile(0.35)
        Q3 = df['method_count'].quantile(0.90)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df_filtered = df[(df['method_count'] >= lower_bound) & (df['method_count'] <= upper_bound)]
        return df_filtered


def simulate_run():
    response = requests.get(
    LoadGenBASE + "load_generator",
    params={"start_date": start_date,"end_date":end_date, "resample_frequency": resample_frequency}
)
    response_data = response.json()
    parsed_data = json.loads(response_data)
    
    predictions = requests.post(PredictorBASE + "predict", 
                      json={"start_date": start_date,
                            "end_date": end_date}
                            )
    predictions_data = predictions.json()
    df_predictions = pd.DataFrame(predictions_data)
    df_predictions['index'] = pd.to_datetime(df_predictions['index'], unit='ms')
    print(df_predictions)

    try:
        df_hourly = pd.DataFrame(parsed_data)  # Convert JSON data to DataFrame
        df_hourly = remove_outliers(df_hourly)
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

    predicted_experienced_loads = []
    predicted_ready_instances = []
    predicted_instances = []

    for load in per_hour_loads:

        if (current_time + step + step) in df_predictions['index'].values:
            future_load = df_predictions.loc[df_predictions['index'] == (current_time + step + step), 'pred'].iloc[0]
        else:
            future_load = None  # No prediction available
        
        service.update(
            current_time=current_time,
            applied_load=load,
            delta_instances=lambda service: calculate_instances(service, None)
        )

        experienced_loads.append(service.experienced_load)
        ready_instances.append(service.count(ServiceInstanceState.READY))
        instances.append(len(service.instances))

        requests.post(LoadRecBASE + "loadrecorder",
                      json={"applied_load": service.applied_load, 
                            "experienced_load": service.experienced_load,
                            "current_time": str(service.current_time),
                            "instances": len(service.instances)})
        #Simulate service update with prediction values aswell
        service.update(
            current_time=current_time,
            applied_load=load,
            delta_instances=lambda service: calculate_instances(service, future_load)
        )
        predicted_experienced_loads.append(service.experienced_load)
        predicted_ready_instances.append(service.count(ServiceInstanceState.READY))
        predicted_instances.append(len(service.instances))

        current_time += step

    hours = [
        i
        for i in range(len(df_hourly))
    ]
    predicted_load_list = df_predictions['pred'].tolist()
    return hours, per_hour_loads, experienced_loads, instances, ready_instances, predicted_load_list, predicted_experienced_loads, predicted_instances, predicted_ready_instances

def plot_loads(
        hours: list[int],
        applied_loads: list[float],
        experienced_loads: list[float],
        total_instances: list[int],
        ready_instances: list[int],
        predicted_load_list: list[float], 
        predicted_experienced_loads: list[float], 
        predicted_instances: list[int], 
        predicted_ready_instances: list[int]
):
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axs[0].plot(hours, experienced_loads, '-r', label='Experienced load (Without Prediction)')
    axs[0].plot(hours, predicted_experienced_loads, '-g', label='Experienced load (With Prediction)')
    axs[0].plot(hours, predicted_load_list, color='orange',  label='Predicted applied Load')
    axs[0].plot(hours, applied_loads, '-b', label='Applied load')
    axs[0].set_ylabel('Load')
    axs[0].grid()
    axs[0].legend()

    axs[1].plot(hours, total_instances, '-r', label='Total instances (Without Prediction)')
    axs[1].plot(hours, predicted_instances, '-g', label='Total instances (With Prediction)')
    axs[1].plot(hours, ready_instances, '-b', label='Ready instances (Without Prediction)')
    axs[1].plot(hours, predicted_ready_instances, color='orange', label='Ready instances (With Prediction)')
    axs[1].set_xlabel('Time (hours)')
    axs[1].set_ylabel('Instances')
    axs[1].grid()
    axs[1].legend()

    plt.tight_layout()
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
    
    


