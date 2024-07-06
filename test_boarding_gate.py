"""Tests for BoardingGateRepl class."""

import pandas as pd

import boarding_gate


class TestBoardingGate:
    """
    Unit tests for the BoardingGateRepl class.

    Use pytest to run.
    """

    reservations_path = "testdata/reservations.jsonl"
    valid_res = pd.DataFrame(
        {
            "passenger_name": ["John Doe", "Chris Knight", "Robert Smith"],
            "flight_number": ["AA311", "AA311", "AA1904"],
            "reservation_code": ["WDXDIC", "ACIWMY", "NAQMBF"],
            "ticket_type": ["General", "General", "General"],
            "seat": ["11-A", "13-D", "6-B"],
        }
    )
    expected_res_df = valid_res.assign(scanned=False).set_index(
        "reservation_code"
    )
    valid_flight = "AA311"
    valid_scan = "WDXDIC"

    # ============== Tests for do_load ==============
    def test_load_valid(self, capsys):
        """Test load command with a valid input."""
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load(self.reservations_path)
        captured = capsys.readouterr()
        assert captured.out == "Loaded 3 reservations.\n"
        pd.testing.assert_frame_equal(gate.reservations, self.expected_res_df)

    def test_load_invalid_path(self, capsys):
        """
        Test load command with an invalid path - warns user but doesn't throw
        error.
        """
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load("invalid/path")
        captured = capsys.readouterr()
        assert captured.out == (
            "Unable to load reservations from invalid/path. Please check the "
            "path.\n"
        )

    def test_load_invalid_data(self, capsys):
        """
        Test load command with invalid reservations data - warns user but
        doesn't throw an error.
        """
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load("testdata/reservations_invalid.jsonl")
        captured = capsys.readouterr()
        assert captured.out == (
            "Reservations data does not contain all required columns.\n"
            "Reservations data failed validation.\n"
        )

    def test_validate_reservations_valid(self):
        """Tests that a valid reservations dataframe passes validation."""
        gate = boarding_gate.BoardingGateRepl()
        assert gate._validate_reservations(self.valid_res)

    def test_validate_reservations_required_columns(self):
        """
        Tests that reservations data without all of the required columns fails
        validation.
        """
        gate = boarding_gate.BoardingGateRepl()
        missing_columns = self.valid_res[
            ["passenger_name", "flight_number", "reservation_code"]
        ]
        extra_columns = pd.concat(
            [
                self.valid_res,
                pd.DataFrame(
                    {
                        "date": ["2024-07-08", "2024-07-09", "2024-07-08"],
                    }
                ),
            ],
            axis=1,
        )
        columns_with_nulls = self.valid_res.copy().replace(
            {"seat": "6-B"}, None
        )
        assert not gate._validate_reservations(missing_columns)
        assert gate._validate_reservations(extra_columns)
        assert not gate._validate_reservations(columns_with_nulls)

    def test_validate_reservations_duplicate_res_code(self):
        """
        Tests that reservations data with duplicate reservation codes fails
        validation.
        """
        gate = boarding_gate.BoardingGateRepl()
        duplicate_res_code = self.valid_res.copy().replace(
            {"reservation_code": "ACIWMY"}, "WDXDIC"
        )
        assert not gate._validate_reservations(duplicate_res_code)

    def test_validate_reservations_invalid_res_code_format(self):
        """
        Tests that reservations data with reservations codes with non
        alphanumeric characters or not exactly 6 characters fail validation.
        """
        gate = boarding_gate.BoardingGateRepl()
        non_alphanum = self.valid_res.copy().replace(
            {"reservation_code": "ACIWMY"}, "ACIWM!"
        )
        too_long = self.valid_res.copy().replace(
            {"reservation_code": "ACIWMY"}, "ACIWMYABC"
        )
        too_short = self.valid_res.copy().replace(
            {"reservation_code": "ACIWMY"}, "ACI"
        )
        not_all_caps = self.valid_res.copy().replace(
            {"reservation_code": "ACIWMY"}, "aciwmy"
        )
        assert not gate._validate_reservations(non_alphanum)
        assert not gate._validate_reservations(too_long)
        assert not gate._validate_reservations(too_short)
        assert not gate._validate_reservations(not_all_caps)

    def test_validate_reservations_non_distinct_seat_assignments(self):
        """
        Test that reservations data with multiple reservations assigned to the
        same seat on the same flight are not allowed.
        """
        gate = boarding_gate.BoardingGateRepl()
        duplicate_seats = self.valid_res.copy().replace(
            {"seat": "13-D"}, "11-A"
        )
        same_seat_different_flight = self.valid_res.copy().replace(
            {"seat": "6-B"}, "11-A"
        )
        assert not gate._validate_reservations(duplicate_seats)
        assert gate._validate_reservations(same_seat_different_flight)

    def test_validate_reservations_invalid_flight_number_format(self):
        """
        Tests that reservations data with flight numbers that are incorrectly
        formatted (not all caps, not alphanumeric, or wrong length) fail
        validation.
        """
        gate = boarding_gate.BoardingGateRepl()
        too_short = self.valid_res.copy().replace(
            {"flight_number": "AA1904"}, "AA"
        )
        too_long = self.valid_res.copy().replace(
            {"flight_number": "AA1904"}, "AA19044444"
        )
        not_alphanum = self.valid_res.copy().replace(
            {"flight_number": "AA1904"}, "AA190!"
        )
        not_all_caps = self.valid_res.copy().replace(
            {"flight_number": "AA1904"}, "aa1904"
        )
        assert not gate._validate_reservations(too_short)
        assert not gate._validate_reservations(too_long)
        assert not gate._validate_reservations(not_alphanum)
        assert not gate._validate_reservations(not_all_caps)

    # ============== Tests for do_flight ==============
    def test_flight_valid(self, capsys):
        """Test flight command with a valid flight number."""
        gate = boarding_gate.BoardingGateRepl()
        gate.do_flight(self.valid_flight)
        captured = capsys.readouterr()
        assert captured.out == "OK\n"
        assert gate.flight == self.valid_flight

        # Changing flight number is allowed.
        gate.do_flight("UA123")
        captured = capsys.readouterr()
        assert captured.out == "OK\n"
        assert gate.flight == "UA123"

        # Lowercase flight numbers get capitalized.
        gate.do_flight("aa311")
        captured = capsys.readouterr()
        assert captured.out == "OK\n"
        assert gate.flight == "AA311"

    def test_flight_invalid(self, capsys):
        """Test invalid flight numbers with non alphanumeric characters."""

        # Spaces aren't allowed.
        gate = boarding_gate.BoardingGateRepl()
        gate.do_flight("AA311 UA123")
        captured = capsys.readouterr()
        assert captured.out == (
            "Expected flight number to be a single alphanumeric word, "
            "e.g. AA311.\n"
        )
        assert gate.flight is None

        # Non-alphanumeric characters like dashes aren't allowed.
        gate.do_flight("AA-311")
        captured = capsys.readouterr()
        assert captured.out == (
            "Expected flight number to be a single alphanumeric word, "
            "e.g. AA311.\n"
        )
        assert gate.flight is None

        # A valid flight number can still be input after an invalid one.
        gate.do_flight(self.valid_flight)
        captured = capsys.readouterr()
        assert captured.out == "OK\n"
        assert gate.flight == self.valid_flight

    # ============== Tests for do_scan ==============
    def test_scan_allow(self, capsys):
        """Test valid scan input leads to ALLOW result."""
        gate = boarding_gate.BoardingGateRepl()
        with capsys.disabled():
            gate.do_load(self.reservations_path)
            gate.do_flight(self.valid_flight)
        gate.do_scan(self.valid_scan)
        captured = capsys.readouterr()
        assert captured.out == "ALLOW\n"

    def test_scan_deny(self, capsys):
        """Test invalid scan input leads to DENY result."""
        gate = boarding_gate.BoardingGateRepl()
        with capsys.disabled():
            gate.do_load(self.reservations_path)
            gate.do_flight(self.valid_flight)
        gate.do_scan("invalid scan")
        captured = capsys.readouterr()
        assert captured.out == "DENY\n"

    def test_scan_no_reservations(self, capsys):
        """
        Test scan without loading in reservations leads to instructing user
        to load reservations first.
        """
        gate = boarding_gate.BoardingGateRepl()
        with capsys.disabled():
            gate.do_flight(self.valid_flight)
        gate.do_scan(self.valid_scan)
        captured = capsys.readouterr()
        assert captured.out == (
            "Please load in the reservation information first with the load"
            " command.\n"
        )

    def test_scan_no_flight(self, capsys):
        """
        Test scan without setting flight first leads to instructing user to
        set the flight number.
        """
        gate = boarding_gate.BoardingGateRepl()
        with capsys.disabled():
            gate.do_load(self.reservations_path)
        gate.do_scan(self.valid_scan)
        captured = capsys.readouterr()
        assert captured.out == (
            "Please set the flight number to board guests for with the "
            "flight command.\n"
        )

    def test_validate_boarding_pass_valid(self):
        """Tests that a valid reservation code passes the validation."""
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load(self.reservations_path)
        gate.do_flight(self.valid_flight)
        assert gate._validate_boarding_pass(self.valid_scan)

    def test_validate_boarding_pass_unknown_code(self):
        """Tests that an unknown reservation code fails validation."""
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load(self.reservations_path)
        gate.do_flight(self.valid_flight)
        assert not gate._validate_boarding_pass("unknown code")

    def test_validate_boarding_pass_already_scanned(self):
        """
        Tests that a reservation code that's already been scanned fails
        validation.
        """
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load(self.reservations_path)
        gate.do_flight(self.valid_flight)
        # First scan passes.
        assert gate._validate_boarding_pass(self.valid_scan)
        # Second scan fails.
        assert not gate._validate_boarding_pass(self.valid_scan)

    def test_validate_boarding_pass_incorrect_flight(self):
        """Tests that a reservation code for the wrong flight is rejected."""
        gate = boarding_gate.BoardingGateRepl()
        gate.do_load(self.reservations_path)
        gate.do_flight(self.valid_flight)
        assert not gate._validate_boarding_pass("NAQMBF")
