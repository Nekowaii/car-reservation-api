# car-reservation-api


Available GraphQL mutations:
- createCar
- updateCar
- deleteCar
- createReservation

### createCar
```
mutation {
  createCar(carData: {carNumber: "C523671934", make: "BMW", model: "X7", branch: {city: "Prague"}}) {
    car {
      carNumber,
      make,
      model
    }
  }
}
```

### updateCar
```
mutation {
  updateCar(carData: {carNumber: "C523671934", make: "BMW", model: "X8"}) {
    car {
      carNumber,
      make,
      model
    }
  }
}
```

### deleteCar
```
mutation {
  deleteCar(carNumber: "C523671934") {
    ok
  }
}
```

### createReservation
```
mutation {
  createReservation(reservationData: 
    {
      startTime: "2023-10-01T17:07:28.930429+00:00", 
      durationMinutes: 2, 
      pickupBranch: {city: "Prague"}, 
      returnBranch: {city: "Prague"}}) 
  {
    reservation {
      car { 
        carNumber, 
        make,
        model
      },
      startTime,
      endTime,
      pickupBranch {
        city
      },
      returnBranch {
        city
      }
    }
  }
}
```