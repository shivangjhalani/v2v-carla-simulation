
# NoBrainCellsLeft: Winning project for CodeRed25 National Level Hackathon conducted by BMSIT, Bangalore

## Problem statement
Develop a real-time IoT system enabling vehicles to exchange critical data such as location, speed, and road conditions to enhance road safety and optimize traffic flow. The system should alert vehicles to sudden stops, road hazards, or traffic changes, reducing accidents and supporting autonomous or semi-autonomous driving. This technology is vital for smart cities, fostering efficient and coordinated urban transportation networks

## Details
There are 2 parts to the project

### 1. digital_simulation
uses carla 9.0.15 to simulate v2v network and collect data. settings.yaml has the whole project configuration.

#### Instructions to run the simulation
- install pip requirements
- Start Carla server
- cd to digital_simulation, python -m src.main
- 2 modes autopilot and manual, give instructions to spectate and control vehicles.
- Tell that it opens a dashboard for each car spawned

### 2. v2v network
- v2v network based on ZigBee communication used to transmit sensor data over the ZigBee protocol
- Each of the ZigBee is configured as either a coordinator which can act as a sender/receiver, an end-device as a receiver which listens over the protocol or a router which can direct and scale the entire network 
- Scales to a mesh network topology of all vehicles in the vicinity
- Run using Python sender and receiver files. Both physical ZigBee should be configured
