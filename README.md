# car-reservation-api


Available GraphQL mutations:
- createCar
- updateCar
- deleteCar
- createReservation
- createReservations

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

### createReservations
```
mutation {
  createReservations(reservationsData: 
    [
      {
        startTime: "2023-10-04T17:39:28.930429+00:00", 
        durationMinutes: 390, 
        pickupBranch: {
          city: "Prague"
        }, 
        returnBranch: {
          city: "Ostrava"
        }
      }, 
      {
        startTime: "2023-10-03T17:39:28.930429+00:00",
        durationMinutes: 390, 
        pickupBranch: {
          city: "Prague"
        }, 
        returnBranch: {
          city: "Prague"
        }
      }, 
      {
        startTime: "2023-10-02T17:39:28.930429+00:00", 
        durationMinutes: 390, 
        pickupBranch: {
          city: "Prague"
        }, 
        returnBranch: {
          city: "Prague"
        }
      }
    ]
  ) 
  {
    reservations {
      car {
        make,
        model
      }
      startTime,
      endTime,
      pickupBranch {
        id
      },
      returnBranch {
        id
      }
    }
  }
}
```