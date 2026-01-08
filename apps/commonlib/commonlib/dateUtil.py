from datetime import datetime

def getSeconds(timeUnit: str):
    """timeUnit: 30s|8m|2h|1h 30m"""
    timeUnit = timeUnit.strip()
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600}
    total_seconds = 0
    parts = timeUnit.split()
    for part in parts:
        part = part.strip()
        if not part: continue
        unit = part[-1].lower()
        if unit in seconds_per_unit:
             total_seconds += int(part[:-1]) * seconds_per_unit[unit]
        else:
             raise ValueError(f"Invalid time string: {part}")
    return total_seconds

def getTimeUnits(seconds: int) -> str:
    """Convert seconds to a detailed time unit string (e.g., 1h 35m 10s)."""
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    time_units = []
    if hours > 0:
        time_units.append(f"{int(hours)}h")
    if minutes > 0:
        time_units.append(f"{int(minutes)}m")
    if seconds > 0 or not time_units:
        time_units.append(f"{int(seconds)}s")
    return ' '.join(time_units)

def getDatetimeNow() -> float:
    return datetime.now().timestamp()

def parseDatetime(timestamp: str) -> float:
    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timestamp()

def getDatetimeNowStr() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
