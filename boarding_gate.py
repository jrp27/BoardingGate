"""A REPL simulation of an airport boarding gate."""

import cmd
import sys
import pandas as pd


class BoardingGateRepl(cmd.Cmd):
    """
    A REPL simulation of an airport boarding gate.

    Accepts commands to load reservation data, set a flight number to board,
    and scan the boarding passes.
    """

    intro = (
        "Welcome to the Boarding Gate Simulator. To start, use the load "
        "command to input a JSONL file of reservation information. Type help "
        " or ? to see all commands."
    )

    reservations = None
    flight = None

    def do_load(self, arg):
        """
        Loads the specified JSONL file of reservation JSON objects.

        Expects the JSON objects to include passenger_name, flight_number,
        reservation_code, ticket_type, and seat fields.
        """
        try:
            with open(arg, encoding="utf-8") as f:
                res = pd.read_json(path_or_buf=f, lines=True, orient="records")
                if not self._validate_reservations(res):
                    print("Reservations data failed validation.")
                    return
                self.reservations = res
                self.reservations = self.reservations.set_index(
                    "reservation_code"
                )
                self.reservations["scanned"] = False
                print(f"Loaded {len(self.reservations)} reservations.")
        except FileNotFoundError:
            print(
                f"Unable to load reservations from {arg}. Please check the "
                "path."
            )

    def do_flight(self, arg):
        """Sets the current flight number that the agent is checking."""
        if not arg.isalnum():
            print(
                "Expected flight number to be a single alphanumeric word, "
                "e.g. AA311."
            )
            return
        self.flight = arg.upper()
        print("OK")

    def do_scan(self, arg):
        """
        Inputs a reservation ID as scanned from a passenger boarding pass.

        Responds with ALLOW if the passenger is allowed to board and DENY
        otherwise.
        """
        if not self._validate_initialized():
            return
        if self._validate_boarding_pass(arg):
            print("ALLOW")
        else:
            print("DENY")

    def do_quit(self, arg):
        """Ends the session and quits the program."""
        print("Goodbye.")
        sys.exit()

    def _validate_reservations(self, res_df):
        """
        Returns true if the given res_df contains valid reservation data.

        The reservation data requirements:
            - Has at least the columns passenger_name, flight_number,
              reservation_code, ticket_type, and seat.
            - No duplicate reservation_codes.
            - All reservation_codes are 6 digit, all caps, alphanumeric strings.
            - All flight numbers are in all caps and alphanumeric.
            - All flight numbers are 4-6 characters long.
            - Per flight number, all seats are distinct.
        """
        if (
            not set(
                [
                    "passenger_name",
                    "flight_number",
                    "reservation_code",
                    "ticket_type",
                    "seat",
                ]
            ).issubset(res_df.columns)
            or res_df[
                [
                    "passenger_name",
                    "flight_number",
                    "reservation_code",
                    "ticket_type",
                    "seat",
                ]
            ]
            .isnull()
            .any()
            .any()
        ):
            print("Reservations data does not contain all required columns.")
            return False
        if (
            not res_df["reservation_code"].is_unique
            or not res_df["reservation_code"].str.isalnum().all()
            or res_df["reservation_code"].str.len().map(lambda l: l != 6).any()
            or not res_df["reservation_code"].str.isupper().all()
        ):
            print("Reservation codes in reservations are not valid.")
            return False
        if (
            not res_df["flight_number"].str.isalnum().all()
            or not res_df["flight_number"].str.isupper().all()
            or res_df["flight_number"]
            .str.len()
            .map(lambda l: l < 4 or l > 6)
            .any()
        ):
            print("Flight numbers in reservations are not valid.")
            return False
        if res_df.duplicated(["flight_number", "seat"]).any():
            print(
                "Per flight, seat assignments are overlapping but should not "
                "be."
            )
            return False
        return True

    def _validate_initialized(self):
        """
        Returns true if reservation data has been loaded and flight number set,
        false otherwise.

        Prompts the user to use the load command if reservations not already
        loaded and the flight command if the flight number is not set.
        """
        if self.reservations is None:
            print(
                "Please load in the reservation information first with the load"
                " command."
            )
            return False
        if self.flight is None:
            print(
                "Please set the flight number to board guests for with the "
                "flight command."
            )
            return False
        return True

    def _validate_boarding_pass(self, res_code):
        """
        Validates the given res_code against the stored reservation data.

        Checks whether the reservation code is present in the dataset,
        corresponds to the current flight, and hasn't already been scanned in.

        Assumes that the reservations data has already been loaded and the
        flight to scan in has already been set.

        Args:
            res_code (string): A 6-digit, alphanumeric reservation code.

        Returns:
            bool: True if the reservation is valid and the passenger can board,
            False otherwise.
        """
        if not res_code in self.reservations.index:
            return False
        res = self.reservations.loc[res_code]
        if res["scanned"]:
            return False
        if res["flight_number"] != self.flight:
            return False
        self.reservations.loc[res_code, "scanned"] = True
        return True


if __name__ == "__main__":
    BoardingGateRepl().cmdloop()
