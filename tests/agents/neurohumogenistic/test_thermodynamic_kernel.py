"""Tests for the Thermodynamic Kernel component."""

import pytest
from unittest.mock import MagicMock, patch

from src.agents.neurohumogenistic.thermodynamic_kernel import (
    PowerDomain,
    PowerReading,
    RAPLReader,
    ThermodynamicKernel,
    ThermodynamicState,
)


class TestPowerReading:
    """Tests for PowerReading dataclass."""

    def test_power_reading_creation(self):
        """Test creating a power reading."""
        reading = PowerReading(
            domain="package-0",
            energy_joules=1000.0,
            power_watts=50.0,
            timestamp=1234567890.0,
            source="rapl",
        )

        assert reading.domain == "package-0"
        assert reading.power_watts == 50.0

    def test_to_otel_attributes(self):
        """Test OTel attribute conversion."""
        reading = PowerReading(
            domain="core",
            energy_joules=500.0,
            power_watts=25.0,
            timestamp=1234567890.0,
            source="rapl",
        )

        attrs = reading.to_otel_attributes()

        assert attrs["power.core.energy_j"] == 500.0
        assert attrs["power.core.power_w"] == 25.0
        assert attrs["power.source"] == "rapl"


class TestThermodynamicState:
    """Tests for ThermodynamicState dataclass."""

    def test_default_state(self):
        """Test default thermodynamic state."""
        state = ThermodynamicState()

        assert state.total_power_watts == 0.0
        assert state.efficiency_eta == 1.0
        assert state.is_cold_snap is False

    def test_to_metrics(self):
        """Test metrics export."""
        state = ThermodynamicState(
            total_power_watts=100.0,
            efficiency_eta=0.85,
            is_cold_snap=True,
        )

        metrics = state.to_metrics()

        assert metrics["thermodynamic.total_power_w"] == 100.0
        assert metrics["thermodynamic.efficiency_eta"] == 0.85
        assert metrics["thermodynamic.cold_snap"] == 1


class TestRAPLReader:
    """Tests for RAPL reader."""

    def test_rapl_unavailable_on_non_linux(self):
        """RAPL should be unavailable when interface doesn't exist."""
        reader = RAPLReader()

        # On non-Linux or without RAPL, should return empty
        readings = reader.read_all_domains()

        # Either returns actual readings or empty list
        assert isinstance(readings, list)


class TestThermodynamicKernel:
    """Tests for the Thermodynamic Kernel."""

    def test_kernel_initialization(self):
        """Test kernel initialization."""
        kernel = ThermodynamicKernel(
            cold_snap_threshold_watts=200.0,
            poll_interval_seconds=1.0,
        )

        assert kernel.cold_snap_threshold == 200.0
        assert kernel.poll_interval == 1.0

    def test_calculate_efficiency_no_readings(self):
        """Efficiency should be 1.0 with no readings."""
        kernel = ThermodynamicKernel()

        efficiency = kernel.calculate_efficiency([])

        assert efficiency == 1.0

    def test_calculate_efficiency_high_power(self):
        """High power should result in lower efficiency."""
        kernel = ThermodynamicKernel()

        readings = [
            PowerReading(
                domain="package-0",
                energy_joules=1000.0,
                power_watts=250.0,  # High power
                timestamp=1234567890.0,
                source="mock",
            )
        ]

        efficiency = kernel.calculate_efficiency(readings)

        # Efficiency should be reduced for high power
        assert efficiency < 1.0

    def test_calculate_efficiency_low_power(self):
        """Low power should result in higher efficiency."""
        kernel = ThermodynamicKernel()

        readings = [
            PowerReading(
                domain="package-0",
                energy_joules=1000.0,
                power_watts=25.0,  # Low power
                timestamp=1234567890.0,
                source="mock",
            )
        ]

        efficiency = kernel.calculate_efficiency(readings)

        # Efficiency should be high for low power
        assert efficiency > 0.8

    def test_check_cold_snap_below_threshold(self):
        """No cold snap when power is below threshold."""
        kernel = ThermodynamicKernel(cold_snap_threshold_watts=200.0)

        is_cold_snap = kernel.check_cold_snap(150.0)

        assert is_cold_snap is False

    def test_enter_cold_snap(self):
        """Test entering cold snap mode."""
        kernel = ThermodynamicKernel()

        kernel.enter_cold_snap()

        assert kernel._state.is_cold_snap is True

    def test_exit_cold_snap(self):
        """Test exiting cold snap mode."""
        kernel = ThermodynamicKernel()
        kernel.enter_cold_snap()

        kernel.exit_cold_snap()

        assert kernel._state.is_cold_snap is False

    def test_should_throttle_in_cold_snap(self):
        """Throttling should be active in cold snap."""
        kernel = ThermodynamicKernel()
        kernel.enter_cold_snap()

        assert kernel.should_throttle() is True

    def test_should_throttle_low_efficiency(self):
        """Throttling should be active with low efficiency."""
        kernel = ThermodynamicKernel()
        kernel._state.efficiency_eta = 0.2

        assert kernel.should_throttle() is True

    def test_register_state_callback(self):
        """Test registering state callbacks."""
        kernel = ThermodynamicKernel()
        callback = MagicMock()

        kernel.register_state_callback(callback)

        assert callback in kernel._state_callbacks

    @pytest.mark.asyncio
    async def test_collect_readings_returns_mock_when_no_sensors(self):
        """Mock readings should be returned when no real sensors."""
        kernel = ThermodynamicKernel()

        readings = await kernel.collect_readings()

        assert len(readings) > 0
        assert readings[0].source == "mock"

    @pytest.mark.asyncio
    async def test_update_state(self):
        """Test state update."""
        kernel = ThermodynamicKernel()

        state = await kernel.update_state()

        assert isinstance(state, ThermodynamicState)
        assert state.total_power_watts >= 0
        assert 0 <= state.efficiency_eta <= 1

    def test_estimate_temperature(self):
        """Test temperature estimation."""
        kernel = ThermodynamicKernel()

        readings = [
            PowerReading(
                domain="package-0",
                energy_joules=1000.0,
                power_watts=100.0,
                timestamp=1234567890.0,
                source="mock",
            )
        ]

        temp = kernel._estimate_temperature(readings)

        # Should be above ambient (25C)
        assert temp > 25.0


class TestMockReadings:
    """Tests for mock reading generation."""

    def test_generate_mock_readings(self):
        """Mock readings should be generated for development."""
        kernel = ThermodynamicKernel()

        readings = kernel._generate_mock_readings()

        assert len(readings) == 3
        domains = {r.domain for r in readings}
        assert "package-0" in domains
        assert "core" in domains
        assert "dram" in domains

    def test_mock_readings_have_realistic_values(self):
        """Mock readings should have realistic power values."""
        kernel = ThermodynamicKernel()

        readings = kernel._generate_mock_readings()

        for reading in readings:
            assert 0 < reading.power_watts < 200
            assert reading.source == "mock"
