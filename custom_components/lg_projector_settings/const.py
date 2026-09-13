"""Constants for the LG Projector Settings integration."""

DOMAIN = "lg_projector_settings"

CONF_HOST = "host"
CONF_KEY = "key"

CONF_HDR_SENSOR = "hdr_sensor"
CONF_HDR_VALUE = "hdr_value"
CONF_DOLBY_VISION_VALUE = "dolby_vision_value"

DEFAULT_HDR_VALUE = "on, true, hdr, hdr10"
DEFAULT_DOLBY_VISION_VALUE = "dolby, dolby_vision, dovi"

# Categorized picture modes for LG WebOS
SDR_MODES = [
    "normal", "standard", "eco", "cinema", "sports", "game", 
    "expert1", "expert2", "filmMaker", "filmmaker", "vivid", "photo", "technicolor"
]

HDR_MODES = [
    "hdrStandard", "hdrCinema", "hdrCinemaBright", "hdrGame", 
    "hdrFilmMaker", "hdrFilmmaker", "hdrVivid", "technicolorHdr"
]

DOLBY_VISION_MODES = [
    "dolbyHdrStandard", "dolbyHdrCinema", "dolbyHdrCinemaBright", 
    "dolbyHdrGame", "dolbyHdrVivid", "dolbyHdrDarkAmazon"
]

# Combined list for initialization if needed
PICTURE_MODES = SDR_MODES + HDR_MODES + DOLBY_VISION_MODES
