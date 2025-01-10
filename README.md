
# NoBrainCellsLeft : 24 hour Hackathon project for CodeRed25 conducted by BMSIT, Bangalore

## Problem statement
Develop a real-time IoT system enabling vehicles to exchange critical data such as location, speed, and road conditions to enhance road safety and optimize traffic flow. The system should alert vehicles to sudden stops, road hazards, or traffic changes, reducing accidents and supporting autonomous or semi-autonomous driving. This technology is vital for smart cities, fostering efficient and coordinated urban transportation networks

## Details
There are 2 parts to the project

### 1. digital_simulation
uses carla 9.0.15 to simulate v2v network and collect data. settings.yaml has whole project configuration.

#### Instructions to run the simulation
- install pip requirements
- Start carla server
- cd to digital_simulation, python -m src.main
- 2 modes autopilot and manual, give instructions to spectate and control vehicles.
- Tell that it opens a dashboard for each car spawned

### 2. v2v network
- v2v netwoerk based on zigb communication used to transmit sensor data over radar.
- Scales to a mesh network topology of all vehicles in vicinity
- Run using python sender and reciever files. Both physical zigbees should be configured