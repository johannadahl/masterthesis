import random
import time

#### OBS denna slutas aldrig köra mo man inte säger nåt så man måste avsluta genom control c

def test_print_numbers():

    seconds =1
    statistics = []
    while True:

        if int(time.time()) % 5 == 0:
            number = random.randint(7, 15)
            print(seconds, f'Every 5 seconds: {number}')
            statistics.append(number)
            print(statistics)


        if int(time.time()) % 5 != 0:
            number = random.randint(0, 3)
            print(seconds, f'Every second: {number}')
            statistics.append(number)
        
        seconds+=1
        # vänta 1 sekund
        time.sleep(1)
        print("sleep")


test_print_numbers()
