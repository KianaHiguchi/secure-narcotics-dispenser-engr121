import network
import socket
import machine
import json
import utime

# Power on temperature sensor supply
machine.Pin(10, machine.Pin.OUT).value(1)

# LED Setup
red_led1 = machine.Pin(14, machine.Pin.OUT)   # dispense
red_led2 = machine.Pin(11, machine.Pin.OUT)   # Temperature danger indicator
green_led1 = machine.Pin(15, machine.Pin.OUT) # Opacity indicator
green_led2 = machine.Pin(13, machine.Pin.OUT) # IR sensor indicator
green_led3 = machine.Pin(12, machine.Pin.OUT) # Temperature status  

# Sensor Setup
light_sensor = machine.ADC(26)
ir_sensor = machine.ADC(27)
temp_sensor = machine.ADC(28)

# Baseline temperature setup
raw_temp_baseline = temp_sensor.read_u16()
voltage_baseline = (raw_temp_baseline / 65535) * 3.3
baseline_temp = 27 - (voltage_baseline - 0.706) / 0.001721
current_temp = baseline_temp

# Light sensor baseline for opacity and thresholds
l_val_baseline = light_sensor.read_u16()
threshold_aspirin = 300
threshold_paracetamol = 2300
threshold_ibuprofen = 5000

# IR sensor threshold for object detection
ir_threshold = 1500
motion_detected = False

# Wi-Fi Access Point
ssid = 'unicorns'
password = 'sparkles'
ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)
while not ap.active():
    utime.sleep_ms(100)
print('Access Point Started', ap.ifconfig())

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Narcotic Dispenser & Organization Device</title>
        <style>
            body { background-color: #ffe0f0; color: black; font-family: Arial, sans-serif; display: flex; flex-direction: column; align-items: center; padding: 20px; }
            header { text-align: center; margin: 20px; }
            .box { background-color: #b3e0ff; border-radius: 10px; width: 80%; max-width: 500px; padding: 20px; margin: 20px 0; display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5); }
            .box h2 { margin: 0 0 10px 0; }
            .medicine-selection input { margin: 10px; cursor: pointer; }
            #dispense-btn { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 18px; margin-top: 20px; }
            #dispense-btn:hover { background-color: #45a049; }
            .medication-list, .temperature, .medicine-status { font-size: 18px; margin-top: 10px; color: #333; }
        </style>
    </head>
    <body>
        <header>
            <h1>Narcotic Dispenser & Organization Device</h1>
        </header>
        <div class="box" id="incoming-medication">
            <h2>Incoming Medication</h2>
            <div class="medication-list" id="medication-list">No data yet.</div>
        </div>
        <div class="box" id="medicine-dispensing">
            <h2>Select Medicine to Dispense</h2>
            <div class="medicine-selection">
                <label><input type="radio" name="medicine" value="Aspirin - 500mg"> Aspirin - 500mg</label><br>
                <label><input type="radio" name="medicine" value="Paracetamol - 250mg"> Paracetamol - 250mg</label><br>
                <label><input type="radio" name="medicine" value="Ibuprofen - 200mg"> Ibuprofen - 200mg</label>
            </div>
            <button id="dispense-btn" onclick="dispenseMedicine()">Dispense Medicine</button>
        </div>
        <div class="box" id="temperature-info">
            <h2>Current Temperature</h2>
            <div class="temperature" id="temperature">Waiting for temperature data...</div>
        </div>
        <script>
            function simulateTemperatureData() {
                fetch("/getTemperature")
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById("temperature").innerText = "Temperature: " + data.temperature + "°C";
                    });
            }

            function dispenseMedicine() {
                const selectedMedicine = document.querySelector('input[name="medicine"]:checked');
                if (selectedMedicine) {
                    const medicine = selectedMedicine.value;
                    alert(`Dispensing: ${medicine}`);
                    fetch(`/dispense?medicine=${medicine}`);  // Request to turn on red_led1
                } else {
                    alert("Please select a medicine to dispense.");
                }
            }

            setInterval(simulateTemperatureData, 5000);  // Update every 5 seconds
        </script>
    </body>
    </html>
    """

def web_page():
    return HTML_PAGE

def handle_request():
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode('utf-8')
        
        # Handle dispense request
        if '/dispense' in request:
            selected_medicine = request.split('medicine=')[1].split(' ')[0] 
            print(f"Dispensing: {selected_medicine}")
            red_led1.value(1) 
            utime.sleep(1)     
            red_led1.value(0)  
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n\r\n"
                + json.dumps({"status": "dispensed", "medicine": selected_medicine})
            )
            conn.sendall(response)
            conn.close()
            return
            
        # Provide temperature
        if "/getTemperature" in request:
            temp_json = json.dumps({"temperature": current_temp})
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n\r\n"
                + temp_json
            )
            conn.sendall(response)
            conn.close()
            return

        # Provide the webpage
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n"
            + web_page()
        )
        conn.sendall(response)
        conn.close()
    except:
        pass

# Create socket server and set a short timeout 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
s.settimeout(0.1)

# Variables LED blinking
last_blink = utime.ticks_ms()
blink_state = 0

# Track current medication being detected by opacity
current_medication = ""

while True:
    handle_request()

    # --- Opacity sensor for green_led1 ---
    current_light_val = light_sensor.read_u16()
    opacity_diff = l_val_baseline - current_light_val
    # print(f"opacity: {opacity_diff}")
    
    if opacity_diff > threshold_ibuprofen:
        blink_delay = 0.1  # fast blink
        current_medication = "Ibuprofen - 200mg"
    elif opacity_diff > threshold_paracetamol:
        blink_delay = 0.5
        current_medication = "Paracetamol - 250mg"
    elif opacity_diff > threshold_aspirin:
        blink_delay = 1.2
        current_medication = "Aspirin - 500mg"
    else:
        blink_delay = None
        current_medication = ""
        
    if len(current_medication) > 1:
        print("Current Medication Detected:", current_medication)
        

    # Blink logic for green_led1
    now = utime.ticks_ms()
    if blink_delay:
        if utime.ticks_diff(now, last_blink) >= int(blink_delay * 1000):
            blink_state = 0 if blink_state else 1
            green_led1.value(blink_state)
            last_blink = now
    else:
        green_led1.value(0)
        blink_state = 0
        last_blink = now

    # --- IR sensor for green_led2 ---
    ir_val = ir_sensor.read_u16()
    if ir_val < ir_threshold and not motion_detected:
        for _ in range(3):
            green_led2.value(1)
            utime.sleep(0.2)
            green_led2.value(0)
            utime.sleep(0.2)
        motion_detected = True
    elif ir_val >= ir_threshold:
        motion_detected = False

    # --- Temperature sensor for green_led3 & red_led2 ---
    raw_temp = temp_sensor.read_u16()
    voltage = (raw_temp / 65535) * 3.3
    current_temp = 27 - (voltage - 0.706) / 0.001721
    temp_diff = abs(current_temp - baseline_temp)
    print("Current temp:", current_temp)
    
    if temp_diff < 3:
        green_led3.value(0)
        red_led2.value(0)
    elif 3 <= temp_diff < 6:
        green_led3.value(1)
        utime.sleep(0.5)
        green_led3.value(0)
        utime.sleep(0.5)
        red_led2.value(0)
    else:
        green_led3.value(0)
        red_led2.value(1)

    utime.sleep(0.1)
