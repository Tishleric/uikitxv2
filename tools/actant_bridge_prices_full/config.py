import os


# Redis connection (producer via Tailscale)
REDIS_HOST: str = os.getenv("REDIS_HOST", "100.83.215.91")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_CHANNEL: str = os.getenv("REDIS_CHANNEL", "spot_risk:prices_full")

# Bridge behavior
DRY_RUN: bool = os.getenv("ACTANT_BRIDGE_DRY_RUN", "true").lower() in {"1", "true", "yes"}
UNDERLYING_BASE: str = os.getenv("UNDERLYING_BASE", "ZN")
MAX_ROWS_PER_UPDATE: int = int(os.getenv("MAX_ROWS_PER_UPDATE", "500"))

# Actant script path (assumed present on Actant machine)
ACTANT_SCRIPTS_PATH: str = os.getenv(
    "ACTANT_SCRIPTS_PATH",
    r"C:\\Program Files\\Actant\\ActProtocols\\Sources\\Public\\Python\\scripts",
)

# Actant connection (defaults provided; override with env as needed)
ACTANT_IP: str = os.getenv("ACTANT_IP", "10.62.6.6")
ACTANT_PORT: int = int(os.getenv("ACTANT_PORT", "4726"))
ACTANT_USER: str = os.getenv("ACTANT_USER", "gautam")
ACTANT_PASSWORD: str = os.getenv("ACTANT_PASSWORD", "password")

# Actant call controls
ACTANT_CALL_TIMEOUT_S: int = int(os.getenv("ACTANT_CALL_TIMEOUT_S", "10"))
ACTANT_RETRY: int = int(os.getenv("ACTANT_RETRY", "1"))

# Allowed expiries filtering (comma-separated tokens found in 'key')
_DEFAULT_ALLOWED = "13AUG25,14AUG25,15AUG25"
_allowed_env = os.getenv("ACTANT_ALLOWED_EXPIRY_TOKENS", _DEFAULT_ALLOWED)
ACTANT_ALLOWED_EXPIRY_TOKENS = [t.strip() for t in _allowed_env.split(",") if t.strip()]

