#Script för att starta alla services samtdigt!
#Alla utom target service, pga den kan va skön att kunna starta och stänga manuellt för att man vill
#göra snabba ändringar

import subprocess
import time
import sys

def start_services():
    try:
        querytool_process = subprocess.Popen(['python3', 'databaseservice/querytool.py'])
        print("Databaseservice module started.")

        load_recorder_process = subprocess.Popen(['python3', 'loadrecorder.py'])
        print("Load Recorder module started.")

        load_generator_process = subprocess.Popen(['python3', 'load_generator.py'])
        print("Load Generator module started.")

        predictive_scaler_process = subprocess.Popen(['python3', 'autoscaler/predictive_scaler.py'])
        print("Predictive scaler module started.")

        time.sleep(5)

        while True:
            pass

    except KeyboardInterrupt:
        print("\nTerminating subprocesses...")
        for process in [querytool_process, load_recorder_process, load_generator_process, predictive_scaler_process]:
            if process.poll() is None:
                process.terminate()
        print("Subprocesses terminated successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_services()