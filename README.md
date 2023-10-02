# car-reservation-api

The Car Reservation API 

## Dependencies
- docker
- python==3.11
- django==4.2.5
- graphene-django==3.1.5

## Getting Started / Installation:
1. Install [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/).
2. Navigate to the project directory: `cd car-reservation-api`
3. Run the application: `docker-compose up`
4. Open in browser `http://127.0.0.1:8000/graphql`

## Testing
To run all of the automation tests in a project: 
```
docker-compose run web python manage.py test
```

## API Usage
The system communicates exclusively via GraphQL. Below are the main GraphQL mutations and queries provided:
- allCars
- upcomingReservations
- createCar
- updateCar
- deleteCar
- createReservation
- createReservations

### allCars
```
query {
  allCars {
    id
    carNumber
    make
    model
  }
}
```

### upcomingReservations
```
query {
  upcomingReservations {
    car {
      carNumber,
      make,
      model
    },
    startTime,
    endTime,
    pickupBranch {
      city
    }
    returnBranch {
      city
    }
  }
}
```

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