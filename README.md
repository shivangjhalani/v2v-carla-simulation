
# NoBrainCellsLeft: Winning project for CodeRed25 National Level Hackathon conducted by BMSIT, Bangalore

## Problem statement
Develop a real-time IoT system enabling vehicles to exchange critical data such as location, speed, and road conditions to enhance road safety and optimize traffic flow. The system should alert vehicles to sudden stops, road hazards, or traffic changes, reducing accidents and supporting autonomous or semi-autonomous driving. This technology is vital for smart cities, fostering efficient and coordinated urban transportation networks

### digital_simulation
uses carla 9.0.15 to simulate v2v network and collect data. settings.yaml has the whole project configuration.

#### Instructions to run the simulation
- install pip requirements
- Start Carla server
- cd to digital_simulation, python -m src.main
- 2 modes autopilot and manual, give instructions to spectate and control vehicles.
- Tell that it opens a dashboard for each car spawned

