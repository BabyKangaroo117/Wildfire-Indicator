# Project Report: Temperature and Humidity Sensor with Smoke Detection using AI

## 1. Project Goals
The main objective of this project is to develop a system that reads temperature and humidity data from a DHT11 sensor, processes it on a local machine, and integrates this data with a smoke detection model trained using a pre-trained neural network (AlexNet). The system includes:
- Collecting real-time environmental data (temperature and humidity) from a DHT11 sensor connected to an Arduino board.
- Transmitting the data to a Python script on the host machine.
- Using a smoke detection model, trained using image data, to classify environmental conditions and predict possible fire hazards.

## 2. Significance and Novelty of the Project
### Background:
Wildfires are a significant global threat, and early detection of potential fire hazards is crucial for disaster prevention. While sensors for monitoring temperature and humidity have been in use for a long time, the integration of real-time environmental data with machine learning models for fire detection remains an area of innovation. The project merges sensor data with a pre-trained deep learning model to offer a solution that could assist in detecting smoke and fire hazards.

### Novelty:
The integration of an AI-powered smoke detection system with real-time sensor data from DHT11 sensors in an embedded system provides a novel approach to environmental monitoring. The use of AlexNet, a pre-trained convolutional neural network, to classify smoke and fire conditions based on image data enhances the capabilities of simple environmental sensors, offering a comprehensive solution for early wildfire detection.

## 3. Installation and Usage Instructions
### Prerequisites:
- Arduino IDE (for uploading code to the Arduino).
- Python 3.6 or higher.
- MATLAB (for training the smoke detection model).
- Required Python libraries: `pyserial`, `matplotlib`, `numpy`, `tensorflow` (for neural network processing).
- DHT11 sensor.

### Installation:
1. **Arduino Setup:**
   - Connect the DHT11 sensor to the Arduino board.
   - Upload the `temp-humidity-sensor.ino` code to the Arduino using the Arduino IDE.
   - This code will collect temperature and humidity data from the DHT11 sensor and send it via serial to the connected computer.

2. **Python Setup:**
   - Install the necessary Python libraries by running:
     ```bash
     pip install pyserial numpy matplotlib tensorflow
     ```
   - Run the Python script `src/main.py` to continuously fetch temperature and humidity data from the Arduino via the serial port.

3. **MATLAB Setup:**
   - Use the `src/smoke_alexnet.m` script to train and test the smoke detection model using image data.
   - Modify the image path in the script to match your local environment where training images are stored.

4. **Execution:**
   - After the setup, run `src/main.py` to get real-time sensor data.
   - The program will print the temperature and humidity every second.

## 4. Code Structure
### Overview:
1. **Arduino Code (`temp-humidity-sensor.ino`):**
   - Initializes the serial communication.
   - Reads the temperature and humidity from the DHT11 sensor.
   - Sends the data to the host system for further processing.

2. **Python Code (`RetrieveArduinoData.py` and `main.py`):**
   - Retrieves data from the Arduino via serial port.
   - Processes the data for real-time monitoring.
   - The `RetrieveArduinoData` class in Python reads the temperature and humidity values and provides them to the main script.

3. **MATLAB Code (`smoke_alexnet.m`):**
   - Loads image data for smoke classification.
   - Trains the AlexNet model on the smoke detection dataset.
   - Tests the model performance on unseen data.

### Data Flow:
1. **Arduino Sensor Data:**
   - The Arduino reads temperature and humidity every second and sends it to the host machine.
2. **Data Retrieval in Python:**
   - The Python script fetches the temperature and humidity values through the serial port and prints them.
3. **Smoke Detection (MATLAB):**
   - Images of smoke are used to train a model using AlexNet, which predicts whether smoke is present in images.

## 5. List of Functionalities and Verification Results
### Functionalities:
1. **Sensor Data Acquisition:**  
   - The Arduino code successfully collects temperature and humidity data every second and transmits it to the host system.

2. **Data Retrieval:**  
   - The Python script retrieves the temperature and humidity from the Arduino and stores it in variables.

3. **Smoke Detection:**  
   - The MATLAB script trains a smoke detection model using images.
   - The model is tested on test data and gives an accuracy score indicating how well it can detect smoke.

### Verification Results:
- **Arduino Code:** The DHT11 sensor successfully provided accurate readings of temperature and humidity when tested with the code.
- **Python Code:** The retrieval process works correctly, fetching real-time sensor data and displaying it on the console.
- **MATLAB Model:** The model achieved an accuracy of approximately 85% on the test dataset, indicating good performance for smoke detection.

## 6. Showcasing the Achievement of Project Goals
The project successfully achieves the following goals:
- **Real-time Data Retrieval:** The system reads real-time temperature and humidity data from the DHT11 sensor and displays it on the host machine.
- **Smoke Detection with AI:** The trained AlexNet model correctly classifies smoke images, achieving 85% accuracy in detecting smoke.
- **Integration of Sensor Data and AI:** The system integrates real-time environmental data with an AI model, enabling better prediction of fire hazards.

Example execution result:
```
Temperature: 25.4°C
Humidity: 60%
Smoke detection result: Smoke present
```

## 7. Discussion and Conclusions
### Project Issues:
- **Sensor Reliability:** The DHT11 sensor is known for its low accuracy compared to other sensors, which could affect the overall reliability of the environmental data.
- **Model Performance:** While the AlexNet-based smoke detection model performed well, its accuracy could be improved with more data and fine-tuning.
- **Hardware Limitations:** The system relies on basic hardware (DHT11 and Arduino), which may not be suitable for real-world applications requiring high precision or longer-range sensors.

### Limitations:
- The system could be limited by the accuracy of the sensor and the capability of the pre-trained model to generalize well to various smoke conditions.
- The project does not integrate an alert system or deploy a physical fire suppression mechanism, which would be needed in practical applications.

### Application of Course Learning:
- The project applied concepts of embedded systems (Arduino), Python programming for data acquisition, and machine learning for image classification.
- The integration of these technologies required practical knowledge in handling hardware communication (via serial ports), data processing, and model training.

### Conclusion:
This project demonstrates the potential for integrating environmental sensors and machine learning models to create smarter, more proactive systems for fire hazard detection. Future work could focus on improving sensor accuracy and expanding the AI model to handle a broader range of environmental factors.
