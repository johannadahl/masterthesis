import random
import time

###### under progress!! testar olika saker 

sample_request = {"load": 12} # ta bort sen, bara för test


def simulated_load(request):

    print("hej test från simulated_load /johanna")
    return random.uniform(0.8, 1.2) * request.get('load', 0) # simulera load baserad på request data



def update_ready_instances():
    return random.randint(1, 5) # detta är endast en random (1-5) för "ready instances"

def process_request(request): # detta är för experimental mode

    print(f"Processing something here for experimental mode request: {request}")
    # nånting här för den faktiska datan


# här e en placeholder för Autoscaler och LoadRecorder classes!!!!
class Autoscaler:
    @staticmethod
    def predict_and_scale(load_data):
        return random.randint(1, 10)

class LoadRecorder:
    @staticmethod
    def get_load_data():
        return [random(2, 20) for _ in range(10)]

class TargetService: #ACTUAL TARGET SERVICE IN SIMULATION MODE
  
    def __init__(self, simulation_mode=False):
        self.simulation_mode = simulation_mode
        self.internal_state = {
            'total_load': 0,
            'scaled_instances': 1,  # Initial number of (scaled) instances
            'ready_instances': 1, # antal instanser som är redo för skalning? 
            # Kanske kommer behövas något mer här?
        }

    # funktion som hanterar requests
    def handle_request(self, request):
   
        if self.simulation_mode:
            self.simulation_mode_behavior(request)
        else:
            self.experimental_mode_behavior(request)


    def simulation_mode_behavior(self, request):
        simulated_load_value = simulated_load(request)
        update_ready_value = update_ready_instances()

        print(f"Simulated Load: {simulated_load_value}")
        print(f"Updated Ready Instances: {update_ready_value}")

        self.internal_state['total_load'] += simulated_load_value
        self.internal_state['ready_instances'] += update_ready_value

    def scale_service(self):
        """
        Scale the service based on the scaling algorithm.
        """
        if not self.simulation_mode:
            # HÄR SKA KUBERNETES ANVÄNDAS???
            new_instances = Autoscaler.predict_and_scale(LoadRecorder.get_load_data())
            self.internal_state['scaled_instances'] = new_instances
            self.internal_state['ready_instances'] = new_instances  # alla instanser samtidigt


target_service = TargetService(simulation_mode=True)
for _ in range(8):  # simulerar 8 requests
    target_service.handle_request(sample_request)
    target_service.scale_service()
    time.sleep(1)  # ändra från 10 det va bara för att matcha förra datan men gick inte
