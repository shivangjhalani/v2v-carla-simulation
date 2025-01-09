const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

app.use(cors());

const PORT = process.env.PORT || 5000;

// Simulated vehicle data
const vehicles = [
  { id: 'V001', state: 'Moving', brakeStatus: 'No', acceleration: 2.5, speed: 60 },
  { id: 'V002', state: 'Stopped', brakeStatus: 'Yes', acceleration: 0, speed: 0 },
];

// Simulated road conditions
const roadConditions = [
  { type: 'Surface', condition: 'Wet' },
  { type: 'Hazard', condition: 'Construction Zone' },
];

// Send updates every 2 seconds
setInterval(() => {
  vehicles.forEach(vehicle => {
    // Simulate changes in vehicle state
    vehicle.speed += (Math.random() - 0.5) * 10;
    vehicle.speed = Math.max(0, Math.min(120, vehicle.speed));
    vehicle.acceleration = (Math.random() - 0.5) * 5;
    vehicle.state = vehicle.speed > 0 ? 'Moving' : 'Stopped';
    vehicle.brakeStatus = Math.random() > 0.7 ? 'Yes' : 'No';
  });

  io.emit('vehicleUpdate', vehicles);
  io.emit('roadConditionUpdate', roadConditions);
}, 2000);

io.on('connection', (socket) => {
  console.log('New client connected');
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

server.listen(PORT, () => console.log(`Server running on port ${PORT}`));

