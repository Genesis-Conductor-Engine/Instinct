"""
Thermodynamic Kernel for Neurohumogenistic Integration

Maps OpenTelemetry ingestion directly to RAPL/IPMI thermodynamic sensors.
Implements the η_thermo (thermodynamic efficiency) metrics for the Diamond Vault UI.

Follows Landauer-Context principles from the Instinct platform:
- Energy-aware computation scheduling
- "Cold Snap" recovery periods for cognitive/computational rest
- Real-time power metrics for workload arbitration
"""

import asyncio
import os
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class PowerDomain(Enum):
    """RAPL power domains."""
    PACKAGE = "package"      # Entire CPU package
    CORE = "core"            # CPU cores only
    UNCORE = "uncore"        # Integrated GPU, memory controller
    DRAM = "dram"            # DRAM (if supported)
    PSYS = "psys"            # Platform-level (if supported)


@dataclass
class PowerReading:
    """A power/energy reading from RAPL or IPMI."""
    domain: str
    energy_joules: float
    power_watts: float
    timestamp: float
    source: str  # "rapl" or "ipmi"

    def to_otel_attributes(self) -> dict:
        """Convert to OpenTelemetry span attributes."""
        return {
            f"power.{self.domain}.energy_j": self.energy_joules,
            f"power.{self.domain}.power_w": self.power_watts,
            "power.source": self.source,
        }


@dataclass
class ThermodynamicState:
    """Current thermodynamic state of the system."""
    total_power_watts: float = 0.0
    total_energy_joules: float = 0.0
    efficiency_eta: float = 1.0
    temperature_celsius: float = 0.0
    is_cold_snap: bool = False
    readings: list[PowerReading] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_metrics(self) -> dict:
        """Export as metrics dictionary for OpenTelemetry."""
        return {
            "thermodynamic.total_power_w": self.total_power_watts,
            "thermodynamic.total_energy_j": self.total_energy_joules,
            "thermodynamic.efficiency_eta": self.efficiency_eta,
            "thermodynamic.temperature_c": self.temperature_celsius,
            "thermodynamic.cold_snap": 1 if self.is_cold_snap else 0,
        }


class RAPLReader:
    """
    Reader for Intel RAPL (Running Average Power Limit) interface.

    Reads energy consumption from /sys/class/powercap/intel-rapl/
    """

    RAPL_BASE_PATH = Path("/sys/class/powercap/intel-rapl")

    def __init__(self):
        self._available = self._check_availability()
        self._last_readings: dict[str, tuple[float, float]] = {}

        if self._available:
            logger.info("rapl.available", path=str(self.RAPL_BASE_PATH))
        else:
            logger.warning("rapl.unavailable", reason="RAPL interface not found")

    def _check_availability(self) -> bool:
        """Check if RAPL interface is available."""
        return self.RAPL_BASE_PATH.exists() and any(self.RAPL_BASE_PATH.iterdir())

    def _read_energy_uj(self, domain_path: Path) -> Optional[float]:
        """Read energy in microjoules from a RAPL domain."""
        energy_file = domain_path / "energy_uj"
        if not energy_file.exists():
            return None

        try:
            with open(energy_file, "r") as f:
                return float(f.read().strip())
        except (PermissionError, IOError) as e:
            logger.debug("rapl.read_error", path=str(energy_file), error=str(e))
            return None

    def _read_max_energy_uj(self, domain_path: Path) -> Optional[float]:
        """Read maximum energy range for wraparound detection."""
        max_file = domain_path / "max_energy_range_uj"
        if not max_file.exists():
            return None

        try:
            with open(max_file, "r") as f:
                return float(f.read().strip())
        except (PermissionError, IOError):
            return None

    def _get_domain_name(self, domain_path: Path) -> str:
        """Get human-readable domain name."""
        name_file = domain_path / "name"
        if name_file.exists():
            try:
                with open(name_file, "r") as f:
                    return f.read().strip()
            except (PermissionError, IOError):
                pass
        return domain_path.name

    def read_all_domains(self) -> list[PowerReading]:
        """Read energy from all available RAPL domains."""
        readings = []

        if not self._available:
            return readings

        current_time = time.time()

        for package_dir in self.RAPL_BASE_PATH.glob("intel-rapl:*"):
            if not package_dir.is_dir():
                continue

            # Read package domain
            package_reading = self._read_domain(package_dir, current_time)
            if package_reading:
                readings.append(package_reading)

            # Read sub-domains (core, uncore, dram)
            for sub_dir in package_dir.glob("intel-rapl:*:*"):
                if sub_dir.is_dir():
                    sub_reading = self._read_domain(sub_dir, current_time)
                    if sub_reading:
                        readings.append(sub_reading)

        return readings

    def _read_domain(self, domain_path: Path, current_time: float) -> Optional[PowerReading]:
        """Read a single RAPL domain and calculate power."""
        domain_name = self._get_domain_name(domain_path)
        energy_uj = self._read_energy_uj(domain_path)

        if energy_uj is None:
            return None

        energy_j = energy_uj / 1_000_000  # Convert to joules

        # Calculate power from delta
        power_watts = 0.0
        domain_key = str(domain_path)

        if domain_key in self._last_readings:
            last_energy, last_time = self._last_readings[domain_key]
            delta_time = current_time - last_time

            if delta_time > 0:
                delta_energy = energy_j - last_energy

                # Handle counter wraparound
                if delta_energy < 0:
                    max_energy = self._read_max_energy_uj(domain_path)
                    if max_energy:
                        delta_energy = (max_energy / 1_000_000) - last_energy + energy_j

                power_watts = delta_energy / delta_time

        self._last_readings[domain_key] = (energy_j, current_time)

        return PowerReading(
            domain=domain_name,
            energy_joules=energy_j,
            power_watts=power_watts,
            timestamp=current_time,
            source="rapl"
        )


class IPMIReader:
    """
    Reader for IPMI (Intelligent Platform Management Interface) sensors.

    Uses ipmitool or direct /dev/ipmi0 access for power metrics.
    """

    def __init__(self, ipmi_host: Optional[str] = None, use_local: bool = True):
        self.ipmi_host = ipmi_host
        self.use_local = use_local
        self._available = self._check_availability()

        if self._available:
            logger.info("ipmi.available", local=use_local, host=ipmi_host)
        else:
            logger.warning("ipmi.unavailable")

    def _check_availability(self) -> bool:
        """Check if IPMI is available."""
        if self.use_local:
            return Path("/dev/ipmi0").exists() or Path("/dev/ipmi/0").exists()
        return self.ipmi_host is not None

    async def read_power_sensors(self) -> list[PowerReading]:
        """Read power-related sensors from IPMI."""
        readings = []

        if not self._available:
            return readings

        try:
            import subprocess

            cmd = ["ipmitool"]
            if self.ipmi_host:
                cmd.extend(["-H", self.ipmi_host, "-U", "admin", "-P", "admin"])
            cmd.extend(["sdr", "type", "Current"])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                readings.extend(self._parse_sdr_output(result.stdout))

        except FileNotFoundError:
            logger.debug("ipmi.ipmitool_not_found")
        except subprocess.TimeoutExpired:
            logger.warning("ipmi.timeout")
        except Exception as e:
            logger.error("ipmi.read_error", error=str(e))

        return readings

    def _parse_sdr_output(self, output: str) -> list[PowerReading]:
        """Parse ipmitool sdr output."""
        readings = []
        current_time = time.time()

        for line in output.strip().split("\n"):
            if not line:
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                sensor_name = parts[0]
                value_str = parts[1]

                # Extract numeric value
                try:
                    value = float("".join(c for c in value_str if c.isdigit() or c == "."))

                    # Assume Watts for power sensors
                    if "watts" in value_str.lower() or "power" in sensor_name.lower():
                        readings.append(PowerReading(
                            domain=sensor_name,
                            energy_joules=0,  # IPMI gives instantaneous power, not energy
                            power_watts=value,
                            timestamp=current_time,
                            source="ipmi"
                        ))
                except ValueError:
                    pass

        return readings


class ThermodynamicKernel:
    """
    Thermodynamic Kernel for the Neurohumogenistic Integration.

    Responsibilities:
    1. Collect RAPL/IPMI power telemetry
    2. Calculate thermodynamic efficiency (η_thermo)
    3. Feed metrics to OpenTelemetry
    4. Manage "Cold Snap" recovery periods
    5. Arbitrate workload based on energy constraints
    """

    def __init__(
        self,
        otel_meter: Optional[Any] = None,
        cold_snap_threshold_watts: float = 200.0,
        cold_snap_duration_seconds: float = 300.0,  # 5 minutes
        poll_interval_seconds: float = 1.0,
    ):
        self.otel_meter = otel_meter
        self.cold_snap_threshold = cold_snap_threshold_watts
        self.cold_snap_duration = cold_snap_duration_seconds
        self.poll_interval = poll_interval_seconds

        self.rapl = RAPLReader()
        self.ipmi = IPMIReader()

        self._state = ThermodynamicState()
        self._running = False
        self._cold_snap_start: Optional[float] = None
        self._state_callbacks: list[Callable[[ThermodynamicState], None]] = []

        # OpenTelemetry instruments
        self._power_gauge = None
        self._energy_counter = None
        self._efficiency_gauge = None

        if otel_meter:
            self._setup_otel_instruments()

        logger.info(
            "thermodynamic_kernel.initialized",
            cold_snap_threshold=cold_snap_threshold_watts,
            poll_interval=poll_interval_seconds
        )

    def _setup_otel_instruments(self) -> None:
        """Set up OpenTelemetry metric instruments."""
        self._power_gauge = self.otel_meter.create_gauge(
            name="instinct.thermodynamic.power_watts",
            description="Current power consumption in watts",
            unit="W"
        )

        self._energy_counter = self.otel_meter.create_counter(
            name="instinct.thermodynamic.energy_joules",
            description="Cumulative energy consumption in joules",
            unit="J"
        )

        self._efficiency_gauge = self.otel_meter.create_gauge(
            name="instinct.thermodynamic.efficiency_eta",
            description="Thermodynamic efficiency ratio (0-1)",
            unit="1"
        )

    def register_state_callback(
        self,
        callback: Callable[[ThermodynamicState], None]
    ) -> None:
        """Register a callback for state updates."""
        self._state_callbacks.append(callback)

    async def collect_readings(self) -> list[PowerReading]:
        """Collect readings from all available sensors."""
        readings = []

        # RAPL readings (synchronous)
        rapl_readings = self.rapl.read_all_domains()
        readings.extend(rapl_readings)

        # IPMI readings (async subprocess)
        ipmi_readings = await self.ipmi.read_power_sensors()
        readings.extend(ipmi_readings)

        # If no real sensors, generate mock data for development
        if not readings:
            readings = self._generate_mock_readings()

        return readings

    def _generate_mock_readings(self) -> list[PowerReading]:
        """Generate mock readings for development/testing."""
        import random
        current_time = time.time()

        return [
            PowerReading(
                domain="package-0",
                energy_joules=current_time * 50,  # Simulated cumulative
                power_watts=45 + random.uniform(-5, 5),
                timestamp=current_time,
                source="mock"
            ),
            PowerReading(
                domain="core",
                energy_joules=current_time * 30,
                power_watts=25 + random.uniform(-3, 3),
                timestamp=current_time,
                source="mock"
            ),
            PowerReading(
                domain="dram",
                energy_joules=current_time * 10,
                power_watts=8 + random.uniform(-1, 1),
                timestamp=current_time,
                source="mock"
            ),
        ]

    def calculate_efficiency(
        self,
        readings: list[PowerReading],
        useful_work: float = 1.0
    ) -> float:
        """
        Calculate thermodynamic efficiency η_thermo.

        η = useful_work / total_energy

        For computational workloads:
        - useful_work = directives processed successfully
        - total_energy = sum of all power readings
        """
        if not readings:
            return 1.0

        total_power = sum(r.power_watts for r in readings)

        if total_power <= 0:
            return 1.0

        # Efficiency relative to Landauer limit
        # Lower power = higher efficiency
        # Normalize to 0-1 range based on expected max (e.g., 300W)
        normalized_power = min(total_power / 300.0, 1.0)

        # Efficiency is inverse of normalized power, scaled by useful work
        efficiency = (1.0 - normalized_power * 0.5) * min(useful_work, 1.0)

        return max(0.0, min(1.0, efficiency))

    def check_cold_snap(self, total_power: float) -> bool:
        """
        Check if system should enter "Cold Snap" recovery mode.

        Cold Snap activates when:
        - Power exceeds threshold for sustained period
        - Or when manually triggered for cognitive recovery
        """
        current_time = time.time()

        if total_power > self.cold_snap_threshold:
            if self._cold_snap_start is None:
                self._cold_snap_start = current_time
                logger.info(
                    "thermodynamic_kernel.cold_snap_pending",
                    power_watts=total_power,
                    threshold=self.cold_snap_threshold
                )
            elif current_time - self._cold_snap_start > 60:  # 1 minute sustained
                return True
        else:
            # Reset if power drops
            if self._cold_snap_start and not self._state.is_cold_snap:
                self._cold_snap_start = None

        return self._state.is_cold_snap

    def enter_cold_snap(self) -> None:
        """Enter Cold Snap recovery mode."""
        self._state.is_cold_snap = True
        self._cold_snap_start = time.time()
        logger.info(
            "thermodynamic_kernel.cold_snap_entered",
            duration=self.cold_snap_duration
        )

    def exit_cold_snap(self) -> None:
        """Exit Cold Snap recovery mode."""
        self._state.is_cold_snap = False
        self._cold_snap_start = None
        logger.info("thermodynamic_kernel.cold_snap_exited")

    async def update_state(self) -> ThermodynamicState:
        """Collect readings and update thermodynamic state."""
        readings = await self.collect_readings()

        total_power = sum(r.power_watts for r in readings)
        total_energy = sum(r.energy_joules for r in readings)
        efficiency = self.calculate_efficiency(readings)

        # Check cold snap
        is_cold_snap = self.check_cold_snap(total_power)

        # Auto-exit cold snap after duration
        if is_cold_snap and self._cold_snap_start:
            if time.time() - self._cold_snap_start > self.cold_snap_duration:
                self.exit_cold_snap()
                is_cold_snap = False

        self._state = ThermodynamicState(
            total_power_watts=total_power,
            total_energy_joules=total_energy,
            efficiency_eta=efficiency,
            temperature_celsius=self._estimate_temperature(readings),
            is_cold_snap=is_cold_snap,
            readings=readings,
            timestamp=time.time()
        )

        # Export to OpenTelemetry
        if self.otel_meter:
            self._export_to_otel()

        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                logger.error("thermodynamic_kernel.callback_error", error=str(e))

        return self._state

    def _estimate_temperature(self, readings: list[PowerReading]) -> float:
        """Estimate temperature from power readings (simplified model)."""
        # Simplified thermal model: T = T_ambient + power * thermal_resistance
        T_ambient = 25.0  # Celsius
        thermal_resistance = 0.5  # Celsius per Watt (simplified)

        total_power = sum(r.power_watts for r in readings)
        return T_ambient + total_power * thermal_resistance

    def _export_to_otel(self) -> None:
        """Export current state to OpenTelemetry."""
        if self._power_gauge:
            self._power_gauge.set(self._state.total_power_watts)

        if self._energy_counter:
            # Counter expects delta, not absolute
            pass  # Would need delta tracking

        if self._efficiency_gauge:
            self._efficiency_gauge.set(self._state.efficiency_eta)

    def get_state(self) -> ThermodynamicState:
        """Get current thermodynamic state."""
        return self._state

    def should_throttle(self) -> bool:
        """Check if workload should be throttled based on thermal state."""
        return (
            self._state.is_cold_snap or
            self._state.efficiency_eta < 0.3 or
            self._state.total_power_watts > self.cold_snap_threshold * 1.5
        )

    async def run(self) -> None:
        """Main polling loop for thermodynamic monitoring."""
        self._running = True
        logger.info("thermodynamic_kernel.started", poll_interval=self.poll_interval)

        while self._running:
            try:
                await self.update_state()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("thermodynamic_kernel.run_error", error=str(e))
                await asyncio.sleep(self.poll_interval)

        logger.info("thermodynamic_kernel.stopped")

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False


def create_otel_provider():
    """
    Create OpenTelemetry meter provider for thermodynamic metrics.

    Returns configured provider that exports to Diamond Vault UI.
    """
    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
            PeriodicExportingMetricReader,
        )

        # Create exporter (console for development, OTLP for production)
        exporter = ConsoleMetricExporter()
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)

        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)

        meter = metrics.get_meter("instinct.thermodynamic", version="0.1.0")

        logger.info("otel.provider_created")
        return meter

    except ImportError:
        logger.warning("otel.not_installed", hint="pip install opentelemetry-sdk")
        return None
