"""Suite registry. Each builder takes a Config and returns a list[Attack]."""
from . import access_control, media_injection, oct2026

BUILDERS = {
    "access_control": access_control.build,
    "media_injection": media_injection.build,
    "oct2026": oct2026.build,
}
