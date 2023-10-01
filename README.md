# car-reservation-api


Available GraphQL mutations:
- createCar
- updateCar
- deleteCar
- createReservation

### createCar
```
mutation {
  createCar(carData: {carNumber: "C244215786", make: "Toyota", model: " Land Cruiser", branch: {city: "Ostrava"}}) {
    car {
      carNumber,
      make,
      model
    },
    carBranchLog {
      branch {
        id,
        city
      },
      timestamp
    }
  }
}
```

### createReservation
```
mutation {
  createReservation(reservationData: 
    {startTime: "2023-10-01T16:01:30+00:00", 
      durationMinutes: 500, 
      pickupBranch: {city: "Ostrava"}, 
      returnBranch: {city: "Prague"}}) 
  {
    ok
  }
}
```