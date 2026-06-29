"""
L-MINER Systems Logic — L0 Safety & L1 Resource Manager
Saad's file.

L0: Safety layer — obstacle detection, always runs first
L1: Resource manager — battery tracking, thermal monitoring
"""

from data_generator import OBSTACLE_MAP

# ─────────────────────────────────────────────
# SYSTEM CONSTANTS
# ─────────────────────────────────────────────

OBSTACLE_THRESHOLD = 0.75      # L0: above this score = unsafe
BATTERY_CAPACITY = 100.0       # %
SCAN_COST = 8.0                # % battery per science scan
MOVE_COST = 2.0                # % battery per rover movement
LOW_POWER_THRESHOLD = 20.0     # % — L1 triggers low power mode
RECHARGE_AMOUNT = 25.0         # % recovered per recharge cycle
MAX_TEMP_C = 50.0              # L1 thermal limit (Celsius, simulated)
NOMINAL_TEMP_C = 28.0          # Starting temperature


# ─────────────────────────────────────────────
# SYSTEM STATE
# Tracks the rover's current status.
# Reset this at the start of each demo run.
# ─────────────────────────────────────────────

class SystemState:
    def __init__(self):
        self.battery = BATTERY_CAPACITY
        self.temperature = NOMINAL_TEMP_C
        self.total_scans = 0
        self.obstacles_detected = 0
        self.low_power_events = 0
        self.recharge_cycles = 0
        self.scan_log = []        # Full history of every cell decision

    def reset(self):
        self.__init__()

    def to_dict(self):
        return {
            "battery": round(self.battery, 1),
            "temperature": round(self.temperature, 1),
            "total_scans": self.total_scans,
            "obstacles_detected": self.obstacles_detected,
            "low_power_events": self.low_power_events,
            "recharge_cycles": self.recharge_cycles,
        }


# ─────────────────────────────────────────────
# L0 — SAFETY LAYER
# Runs first. If unsafe, nothing else runs.
# ─────────────────────────────────────────────

def l0_safety_check(row, col):
    """
    L0: Check if a cell is safe to enter and scan.

    Uses pre-assigned obstacle scores from the terrain map.
    In a real system this would use stereo camera depth maps.

    Returns:
        safe: bool
        obstacle_score: float (0-1)
        status_msg: human readable status
    """
    obstacle_score = float(OBSTACLE_MAP[row, col])
    safe = obstacle_score <= OBSTACLE_THRESHOLD

    if safe:
        status_msg = (
            f"L0 ✅ SAFE — Obstacle score: {obstacle_score:.2f} "
            f"(threshold: {OBSTACLE_THRESHOLD})"
        )
    else:
        status_msg = (
            f"L0 ⛔ UNSAFE — Obstacle score: {obstacle_score:.2f} "
            f"exceeds threshold {OBSTACLE_THRESHOLD}. Skipping cell."
        )

    return {
        "safe": safe,
        "obstacle_score": obstacle_score,
        "status": "SAFE" if safe else "OBSTACLE DETECTED",
        "status_msg": status_msg,
        "layer": "L0"
    }


# ─────────────────────────────────────────────
# L1 — RESOURCE MANAGER
# Runs after L0 clears. Manages battery + thermal.
# ─────────────────────────────────────────────

def l1_resource_check(state: SystemState):
    """
    L1: Check if resources allow a science scan.

    Args:
        state: current SystemState object

    Returns dict with decision and updated state info.
    """
    # Simulate temperature rising slightly with each scan
    # (electronics heat up during operation)
    current_temp = state.temperature

    # Check battery
    if state.battery < LOW_POWER_THRESHOLD:
        return {
            "can_scan": False,
            "reason": "LOW BATTERY",
            "battery": round(state.battery, 1),
            "temperature": round(current_temp, 1),
            "status": (
                f"L1 ⚡ LOW POWER — Battery at {state.battery:.1f}%. "
                f"Minimum required: {LOW_POWER_THRESHOLD}%. "
                f"Entering recharge mode."
            ),
            "layer": "L1"
        }

    # Check thermal
    if current_temp > MAX_TEMP_C:
        return {
            "can_scan": False,
            "reason": "THERMAL LIMIT",
            "battery": round(state.battery, 1),
            "temperature": round(current_temp, 1),
            "status": (
                f"L1 🌡️ THERMAL LIMIT — Temperature {current_temp:.1f}°C "
                f"exceeds {MAX_TEMP_C}°C. Cooling down."
            ),
            "layer": "L1"
        }

    return {
        "can_scan": True,
        "reason": "OK",
        "battery": round(state.battery, 1),
        "temperature": round(current_temp, 1),
        "status": (
            f"L1 ✅ RESOURCES OK — Battery: {state.battery:.1f}% | "
            f"Temp: {current_temp:.1f}°C"
        ),
        "layer": "L1"
    }


# ─────────────────────────────────────────────
# STATE UPDATES
# Called after each action to update system state.
# ─────────────────────────────────────────────

def consume_scan_power(state: SystemState):
    """Deduct battery for a science scan."""
    state.battery = max(0.0, state.battery - SCAN_COST)
    state.temperature = min(MAX_TEMP_C + 5,
                            state.temperature + 1.5)  # heats up
    state.total_scans += 1
    return state


def consume_move_power(state: SystemState):
    """Deduct battery for rover movement."""
    state.battery = max(0.0, state.battery - MOVE_COST)
    return state


def recharge(state: SystemState):
    """
    Recharge battery during a solar window.
    Also cools down electronics.
    """
    state.battery = min(BATTERY_CAPACITY,
                        state.battery + RECHARGE_AMOUNT)
    state.temperature = max(NOMINAL_TEMP_C,
                            state.temperature - 8.0)
    state.recharge_cycles += 1
    return state


# ─────────────────────────────────────────────
# FULL DECISION PIPELINE
# Combines L0 + L1 for one cell.
# Called by dashboard for each scan step.
# ─────────────────────────────────────────────

def process_cell(row, col, state: SystemState):
    """
    Run the full L0 → L1 decision pipeline for one cell.

    Args:
        row, col: grid position
        state: current SystemState

    Returns dict with full decision breakdown.
    """
    result = {
        "row": row,
        "col": col,
        "l0": None,
        "l1": None,
        "proceed_to_l2": False,
        "skip_reason": None,
    }

    # Move to cell (costs battery regardless)
    consume_move_power(state)

    # ── L0 Check ──
    l0 = l0_safety_check(row, col)
    result["l0"] = l0

    if not l0["safe"]:
        result["skip_reason"] = "L0: Obstacle Detected"
        state.obstacles_detected += 1
        state.scan_log.append({
            "cell": (row, col),
            "decision": "SKIPPED",
            "reason": "Obstacle"
        })
        return result

    # ── L1 Check ──
    l1 = l1_resource_check(state)
    result["l1"] = l1

    if not l1["can_scan"]:
        result["skip_reason"] = f"L1: {l1['reason']}"
        state.low_power_events += 1
        state.scan_log.append({
            "cell": (row, col),
            "decision": "SKIPPED",
            "reason": l1["reason"]
        })
        return result

    # ── All clear — L2 can run ──
    result["proceed_to_l2"] = True
    consume_scan_power(state)
    state.scan_log.append({
        "cell": (row, col),
        "decision": "SCANNED",
        "battery_after": state.battery
    })

    return result


# ─────────────────────────────────────────────
# QUICK TEST — run this file directly
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("L-MINER Systems Logic (L0/L1) — Verification Test")
    print("=" * 50)

    state = SystemState()

    print(f"\n[Initial State]")
    print(f"  Battery    : {state.battery}%")
    print(f"  Temperature: {state.temperature}°C")

    print("\n[1] Testing L0 — Safe cell (0,1):")
    l0 = l0_safety_check(0, 1)
    print(f"    {l0['status_msg']}")

    print("\n[2] Testing L0 — Obstacle cell (0,3):")
    l0 = l0_safety_check(0, 3)
    print(f"    {l0['status_msg']}")

    print("\n[3] Testing L1 — Normal battery:")
    l1 = l1_resource_check(state)
    print(f"    {l1['status']}")

    print("\n[4] Simulating battery drain to trigger L1...")
    state.battery = 15.0
    l1 = l1_resource_check(state)
    print(f"    {l1['status']}")

    print("\n[5] Recharging...")
    state = recharge(state)
    print(f"    Battery after recharge: {state.battery}%")
    print(f"    Temperature after cool: {state.temperature}°C")

    print("\n[6] Full pipeline test — scanning 6 cells:")
    state.reset()
    test_cells = [(0, 1), (0, 3), (1, 0), (1, 2), (2, 0), (3, 3)]

    for row, col in test_cells:
        decision = process_cell(row, col, state)
        if decision["proceed_to_l2"]:
            print(f"  Cell ({row},{col}): ✅ PROCEED TO L2 | "
                  f"Battery: {state.battery:.1f}%")
        else:
            print(f"  Cell ({row},{col}): ⛔ SKIPPED — "
                  f"{decision['skip_reason']}")

    print(f"\n  Final State: {state.to_dict()}")

    print("\n✅ L0/L1 logic working correctly.")
    print("   Next step: run dashboard.py (Hajra)")
