# Enterprise Transport & Fleet Management (ETFM) Documentation

This document describes the fleet vehicles registries, routing, scheduled runs, passenger boarding, and GPS location telemetry of the **transport** app.

---

## 1. Fleet & Drivers
- **Vehicle**: Registration plate values and capacity bounds.
- **Driver**: Licensing records extending base Person IDs.

---

## 2. Transit Paths & Schedules
- **Route**: Start and end coordinates with mileage scales.
- **RouteStop**: Sequential pickup locations.
- **Trip**: Morning or afternoon scheduled bus dispatch runs.
- **TripPassenger**: Check-ins marks logging when student boards.

---

## 3. Operations & GPS
- **VehicleLocation**: GPS points tracking.
- **FuelLog**: refueling audits.
- **MaintenanceSchedule**: Servicing planners.

---

## 4. REST APIs
Endpoints are mapped under `/transport/api/v1/`:
- `GET/POST /transport/routes/`: Route outlines list.
- `GET/POST /transport/trips/`: Dispatch loops.
- `GET/POST /transport/gps/`: Location coordinates cache.
