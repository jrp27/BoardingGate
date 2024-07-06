# Airport Boarding Gate

Jeanie Pearson-Wanek

## Usage Instructions

### Required Packages

* pandas (`pip install pandas`)
* pytest - to run tests (`pip install pytest`)

### To Run

1. Check out repo
2. Run the REPL simulator:
    * From the BoardingGate directory:
        `python3 boarding_gate.py`
3. Run the tests:
    * From the BoardingGate directory:
        `pytest`

## Design Choices

Assumptions:
* Reservations data fits in memory.
* `reservation_code` is unique across flights, passengers, etc, and thus can be used as the primary key.
    * It may be reasonable to include the last name as part of the primary key, given the space of `reservation_code`s is only 35^6. For now that is not implemented.
* Valid reservations data meets the following requirements:
    * Has at least the columns passenger_name, flight_number, reservation_code,
    ticket_type, and seat.
    * No duplicate reservation_codes.
    * All reservation_codes are 6 digit, all caps, alphanumeric strings.
    * All flight numbers are in all caps and alphanumeric.
    * All flight numbers are 4-6 characters long.
    * Per flight number, all seats are distinct.
* A given reservation and flight number code can only be scanned in once.

Rules for valid boarding:
* The `reservation_code` must be present in the dataset.
* The associated `flight_number` must be the one being currently scanned in.
* The `reservation_code` must never have been encountered before.

External librarys rationale:
* I used the pandas library to store the reservations data as a
  Dataframe. This enables simple and performant manipulation of
  the reservations (particularly useful when validating the input).
* I used pytest for the unit testing. This makes it easy to validate the stdout
  content displayed by the REPL, in addition to the correctness of the
  reservation loading and code scanning logic.