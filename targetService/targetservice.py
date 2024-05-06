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
import numpy as np
from scipy.stats import norm
import statistics


app = Flask(__name__)
api = Api(app)
LoadGenBASE = "http://127.0.0.1:8009/"
LoadRecBASE = "http://127.0.0.1:8008/"
PredictorBASE = "http://127.0.0.1:8010/"

SCALING_THRESHOLD = 0.2
DESIRED_MEAN_LOAD = 0.5
SCALE_UP_TIME = ScalingTimeOptions(mean_time=timedelta(minutes=60), std_dev=timedelta(minutes=0.01))
SCALE_DOWN_TIME = ScalingTimeOptions(mean_time=timedelta(minutes=60), std_dev=timedelta(minutes=0.01))

class TargetService(Resource):

    def __init__(
            self, 
            applied_load: 0, 
            current_time: datetime,
            scale_up_time: ScalingTimeOptions,
            scale_down_time: ScalingTimeOptions,
            starting_instances: int = 0,
            ready_instances: int = 0,
            instance_load: float = 1,
            instance_baseline_load: float = 0.01,
            starting_load: float = 0.2,
            terminating_load: float = 0.2,
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
               delta_instances: int| Callable[[TargetService], int]):
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
        service: TargetService, future_load: float
) -> int:
    processed_load = service.processed_load
    process_capability = service.total_load_capability

    process_utilization = 0 if processed_load == 0 else \
        processed_load / process_capability

    
    upper_threshold = DESIRED_MEAN_LOAD + SCALING_THRESHOLD
    lower_threshold = DESIRED_MEAN_LOAD - 0.09

    scaling_factor_future = None
    if future_load is not None:
        future_processed_load = min(future_load, process_capability)
        future_process_utilization = future_processed_load / process_capability
        scaling_factor_future = future_process_utilization / DESIRED_MEAN_LOAD

        if lower_threshold < process_utilization < upper_threshold:
            if lower_threshold < future_process_utilization < upper_threshold:
                return 0
    else: 
        if lower_threshold < process_utilization < upper_threshold:
           return 0
        
    scaling_factor = process_utilization / DESIRED_MEAN_LOAD

    if scaling_factor_future is not None:
        if scaling_factor_future > 1 or scaling_factor > 1:
            scaling_factor = max(scaling_factor, scaling_factor_future)
        else:
            #Sätt min om man vill va agressiv och max om man vill vara säker
            scaling_factor = min(scaling_factor, scaling_factor_future)

    current_instances = service.count(ServiceInstanceState.READY)
    starting_instances = service.count(ServiceInstanceState.STARTING)
    terminating_instances = service.count(ServiceInstanceState.TERMINATING)

    down_instances = math.ceil(
        (current_instances - terminating_instances) * (1 - scaling_factor)
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
        Q3 = df['method_count'].quantile(0.80)

        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df_filtered = df[(df['method_count'] >= lower_bound) & (df['method_count'] <= upper_bound)]
        return df_filtered

def rolling_average(data: list[float], radius: int) -> list[float]:
    return [
        average(data, index, radius)
        for index in range(len(data))
    ]

def average(data: list[float], index: int, radius: int):
    total = 0.0
    total_count = 0

    start = max(0, index - radius)
    stop = min(index + radius, len(data) - 1)

    for i in range(start, stop):
        weight = radius - abs(index - i)
        total += data[i] * weight
        total_count += weight

    return total / total_count

def weighted_average_load(predictions_data: pd.DataFrame, target_time: pd.Timestamp, mean_time: int, std_dev_minutes: int):
    mean_time = pd.Timedelta(minutes=mean_time)
    start_time = target_time + mean_time - pd.Timedelta(minutes=std_dev_minutes)
    end_time = target_time + mean_time + pd.Timedelta(minutes=std_dev_minutes)

    window_predictions = predictions_data[(predictions_data['index'] >= start_time) & (predictions_data['index'] <= end_time)]

    #weights = norm.pdf((window_predictions['index'] - target_time + mean_time) / pd.Timedelta(minutes=std_dev_minutes))*weight_scale
    time_diffs = (window_predictions['index'] - (target_time + mean_time)  ) / pd.Timedelta(minutes=std_dev_minutes)
    
    mean_time_minutes = mean_time.total_seconds() / 60  # Convert to minutes
    weights = norm.pdf(time_diffs, loc=mean_time_minutes, scale=std_dev_minutes)

    weighted_avg_load = np.average(window_predictions['pred'], weights=weights)

    return weighted_avg_load

def get_minut_df(parsed_data):
    df_parsed = pd.DataFrame(parsed_data) 
    df_parsed['time'] = pd.to_datetime(df_parsed['time'], unit='ms')
    
    df_minutes = df_parsed.copy()
    last_row_timestamp = df_minutes.iloc[-1]['time'].date()
    end_date_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    if last_row_timestamp == end_date_date:
        df_minutes = df_minutes.iloc[:-1]  #Remove the last row. Detta görs för att annars kan de bli oklar bugg :)

    #TO GET THE ROLLING AVARAGE PER MINUTE 
    df_minutes["method_count"] = rolling_average(df_minutes["method_count"].to_list(), 60)
    print("Df parsed,",df_minutes)
    return df_minutes

def simulate_run_minutes():
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
    if 'pred' not in df_predictions.columns:
        df_predictions['pred'] = None

    df_minutes =  get_minut_df(parsed_data)
  #  df_minutes = remove_outliers(df_minutes)
        
    per_minute_loads = df_minutes["method_count"] 

    current_time = df_minutes['time'].iloc[0]
    step = timedelta(minutes=1)
    future_step = timedelta(minutes=70)

    service = TargetService(
        current_time=current_time,
        applied_load=per_minute_loads[0],
        scale_up_time=SCALE_UP_TIME,
        scale_down_time=SCALE_DOWN_TIME,
        ready_instances=40
    )
    service_accuracy_differences = []
    service_squared_accuracy_differences = []

    future_service = TargetService(
        current_time=current_time,
        applied_load=per_minute_loads[0],
        scale_up_time=SCALE_UP_TIME,
        scale_down_time=SCALE_DOWN_TIME,
        ready_instances=40
    )
    future_service_accuracy_differences = []
    future_service_squared_accuracy_differences = []

    experienced_loads = []
    ready_instances = []
    instances = []
    downtime_occurances = 0

    predicted_experienced_loads = []
    predicted_ready_instances = []
    predicted_instances = []
    prediction_downtime_occurances = 0
    

    for load in per_minute_loads:
        current_time += step

        if (current_time + future_step) in df_predictions['index'].values and not df_predictions['pred'].isnull().all():
            """
            Det är alltså här vi titttar in på framtida värden!
            Just nu är den satt på 30 min+-5min fram, alltså viktade avarage pland prediktade värden 20-50 fram
            """
            future_load = weighted_average_load(df_predictions, current_time, 30, 5) 
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
        service_accuracy_differences.append(calculate_differences(service))
        service_squared_accuracy_differences.append(calculate_squared_differences(service))

        ##Downtime Check
        if check_downtime(service):
            downtime_occurances += 1

        #DET HÄR ÄR UTKOMMENTERAT PGA TAR FÖR LÅNG TID
        #Detta är delen som recordar allt som servicen gör till databasen, alltså lagrar historisk data
      #  requests.post(LoadRecBASE + "loadrecorder",
      #                json={"applied_load": service.applied_load, 
      #                      "experienced_load": service.experienced_load,
      #                      "current_time": str(service.current_time),
      #                      "instances": len(service.instances)})
        #Simulate service update with prediction values aswell
        future_service.update(
            current_time=current_time,
            applied_load=load,
            delta_instances=lambda future_service: calculate_instances(future_service, future_load)
        )
        predicted_experienced_loads.append(future_service.experienced_load)
        predicted_ready_instances.append(future_service.count(ServiceInstanceState.READY))
        predicted_instances.append(len(future_service.instances))
        future_service_accuracy_differences.append(calculate_differences(future_service))
        future_service_squared_accuracy_differences.append(calculate_squared_differences(future_service))
        ##Downtime Check
        if check_downtime(future_service):
            prediction_downtime_occurances += 1
        
    minutes = [
        i
        for i in range(len(df_minutes))
    ]
    predicted_load_list = df_predictions['pred'].tolist()
    print(df_predictions)

    service_accuracy = calculate_scaling_accuracy(service_accuracy_differences)
    service_squared_accuracy = calculate_scaling_accuracy(service_squared_accuracy_differences)
    future_service_accuracy = calculate_scaling_accuracy(future_service_accuracy_differences)
    future_service_squared_accuracy = calculate_scaling_accuracy(future_service_squared_accuracy_differences)
    uptime_percentage = calculate_uptime_percentage(len(df_minutes), downtime_occurances)
    prediction_uptime_percentage = calculate_uptime_percentage(len(df_minutes), prediction_downtime_occurances)

    print("Scaling Accuracy without prediction:", round(service_accuracy,2), " and using squared differences:", round(service_squared_accuracy,2))
    print("minuter av downtime", downtime_occurances)
    print("uptime percentage: {:.1%}".format(uptime_percentage))  

    print("Scaling Accuracy with prediction:", round(future_service_accuracy,2),  " and using squared differences:", round(future_service_squared_accuracy,2))
    print("minuter av downtime", prediction_downtime_occurances)
    print("uptime percentage: {:.1%}".format(prediction_uptime_percentage))  
    return minutes, per_minute_loads, experienced_loads, instances, ready_instances, predicted_load_list, predicted_experienced_loads, predicted_instances, predicted_ready_instances

def plot_loads_minutes(
        minutes: list[int],
        applied_loads: list[float],
        experienced_loads: list[float],
        total_instances: list[int],
        ready_instances: list[int],
        predicted_load_list: list[float], 
        predicted_experienced_loads: list[float], 
        predicted_instances: list[int], 
        predicted_ready_instances: list[int]

        
):

    import matplotlib.dates as mdates

    fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axs[0].plot(minutes, experienced_loads, '-r', label='Experienced load (Without Prediction)')
    axs[0].plot(minutes, predicted_experienced_loads, '-g', label='Experienced load (With Prediction)')
    axs[0].plot(minutes, applied_loads, '-b', label='Applied load')
    axs[0].plot(predicted_load_list, color='orange',  label='Predicted applied Load')
    axs[0].set_ylabel('Load')
    axs[0].grid()
    axs[0].legend()

    axs[1].plot(minutes, ready_instances, '-b', label='Ready instances (Without Prediction)')
    axs[1].plot(minutes, predicted_ready_instances, color='orange', label='Ready instances (With Prediction)')
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('Instances')
    axs[1].grid()
    axs[1].legend()

    axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    #försöka lägga till här vilken modell/data som används
    plt.suptitle('Simulation using model X and data Y')

    plt.tight_layout()
    plt.show()


def calculate_total_load_capability(service: TargetService):
    total_load_capability = 0
    constant_loads = {
            ServiceInstanceState.STARTING: service.starting_load,
            ServiceInstanceState.READY: service.instance_baseline_load,
            ServiceInstanceState.TERMINATING: service.terminating_load
        }

    for instance in service.instances:
        constant_load = constant_loads.get(instance.state) or 0
        total_load_capability += instance.load_capability - constant_load
    
    return total_load_capability

def calculate_differences(service: TargetService) -> float:
    """
    Difference between the number of instances and the number of instances required to meet the load.
    """
    optimal_load_capacity = service.applied_load
    optimal_instance_count = (optimal_load_capacity / service.instance_load_capability)/DESIRED_MEAN_LOAD
    current_instance_count = service.count(ServiceInstanceState.READY)
    error = abs(optimal_instance_count - current_instance_count)
    return error

def calculate_scaling_accuracy(differences: list[float]) -> float:
    """
    Scaling accuracy - The average difference.
    """
    mean_difference = statistics.mean(differences)
    return mean_difference

def calculate_squared_differences(service: TargetService) -> float:
    """
    Squared difference between the number of instances and the number of instances required to meet the load.
    -> giving more importance to larger errors. 
    """
    optimal_load_capacity = service.applied_load
    optimal_instance_count = (optimal_load_capacity / service.instance_load_capability) * 2
    current_instance_count = service.count(ServiceInstanceState.READY)
    squared_error = (optimal_instance_count - current_instance_count) ** 2
    return squared_error

def check_downtime(service: TargetService)-> bool:
    """
    Checks if the system can't meet the load during that minute. 
    """
    processed_load = service.processed_load
    applied_load = service.applied_load
    if processed_load < applied_load:
        return True
    else:  
        return False

def calculate_uptime_percentage(total_time: int, downtime: int) -> float:
    """
    Percentage measure on how much of the total simulation the service could handle the applied load.
    """
    downtime_percentage = downtime/total_time
    uptime_percentage = 1 - downtime_percentage
    return uptime_percentage

def main():
    args = simulate_run_minutes()
    plot_loads_minutes(*args)

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
    
    


