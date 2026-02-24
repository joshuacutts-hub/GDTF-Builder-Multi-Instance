"""
GDTF 1.1 Builder — Manual Entry
MA3 / Vectorworks / Capture / Onyx compatible
"""

import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile, io, uuid, re, copy

# ══════════════════════════════════════════════════════════════════════════════
#  GDTF ATTRIBUTE MAP
# ══════════════════════════════════════════════════════════════════════════════
ATTR_MAP = {
    "dimmer":           ("Dimmer",              "Dimming",  "Intensity", "Dimmer"),
    "intensity":        ("Dimmer",              "Dimming",  "Intensity", "Dimmer"),
    "master":           ("Dimmer",              "Dimming",  "Intensity", "Dimmer"),
    "pan":              ("Pan",                 "Position", "Position",  "PanTilt"),
    "tilt":             ("Tilt",                "Position", "Position",  "PanTilt"),
    "pan speed":        ("PanRotate",           "Position", "Position",  "PanTilt"),
    "tilt speed":       ("TiltRotate",          "Position", "Position",  "PanTilt"),
    "red":              ("ColorAdd_R",          "Color",    "Color",     "RGB"),
    "green":            ("ColorAdd_G",          "Color",    "Color",     "RGB"),
    "blue":             ("ColorAdd_B",          "Color",    "Color",     "RGB"),
    "white":            ("ColorAdd_W",          "Color",    "Color",     "RGBW"),
    "amber":            ("ColorAdd_A",          "Color",    "Color",     "RGBW"),
    "lime":             ("ColorAdd_L",          "Color",    "Color",     "RGBW"),
    "uv":               ("ColorAdd_UV",         "Color",    "Color",     "RGBW"),
    "indigo":           ("ColorAdd_I",          "Color",    "Color",     "RGBW"),
    "cyan":             ("ColorSub_C",          "Color",    "Color",     "CMY"),
    "magenta":          ("ColorSub_M",          "Color",    "Color",     "CMY"),
    "yellow":           ("ColorSub_Y",          "Color",    "Color",     "CMY"),
    "cto":              ("CTO",                 "Color",    "Color",     "CTO"),
    "ctb":              ("CTB",                 "Color",    "Color",     "CTB"),
    "hue":              ("CIE_X",              "Color",    "Color",     "HSB"),
    "saturation":       ("CIE_Y",              "Color",    "Color",     "HSB"),
    "color wheel":      ("Color1",             "Color",    "Color",     "ColorWheel"),
    "colour wheel":     ("Color1",             "Color",    "Color",     "ColorWheel"),
    "color":            ("Color1",             "Color",    "Color",     "ColorWheel"),
    "colour":           ("Color1",             "Color",    "Color",     "ColorWheel"),
    "color mix":        ("ColorMixMode",       "Color",    "Color",     "ColorWheel"),
    "shutter":          ("Shutter1",           "Beam",     "Beam",      "Shutter"),
    "strobe":           ("Shutter1Strobe",     "Beam",     "Beam",      "Shutter"),
    "strobe rate":      ("Shutter1StrobeFreq", "Beam",     "Beam",      "Shutter"),
    "strobe speed":     ("Shutter1StrobeFreq", "Beam",     "Beam",      "Shutter"),
    "zoom":             ("Zoom",               "Beam",     "Beam",      "Zoom"),
    "focus":            ("Focus1",             "Beam",     "Beam",      "Focus"),
    "iris":             ("Iris",               "Beam",     "Beam",      "Iris"),
    "frost":            ("Frost1",             "Beam",     "Beam",      "Frost"),
    "diffusion":        ("Frost1",             "Beam",     "Beam",      "Frost"),
    "gobo":             ("Gobo1",             "Gobo",     "Gobo",      "Gobo"),
    "gobo wheel":       ("Gobo1",             "Gobo",     "Gobo",      "Gobo"),
    "gobo 1":           ("Gobo1",             "Gobo",     "Gobo",      "Gobo"),
    "gobo 2":           ("Gobo2",             "Gobo",     "Gobo",      "Gobo"),
    "gobo rotation":    ("Gobo1Pos",          "Gobo",     "Gobo",      "Gobo"),
    "gobo spin":        ("Gobo1PosRotate",    "Gobo",     "Gobo",      "Gobo"),
    "gobo index":       ("Gobo1Pos",          "Gobo",     "Gobo",      "Gobo"),
    "prism":            ("Prism1",            "Beam",     "Beam",      "Prism"),
    "prism rotation":   ("Prism1Pos",         "Beam",     "Beam",      "Prism"),
    "effects":          ("Effects1",          "Beam",     "Beam",      "Effects"),
    "effect":           ("Effects1",          "Beam",     "Beam",      "Effects"),
    "animation":        ("Effects1",          "Beam",     "Beam",      "Effects"),
    "effects speed":    ("EffectsSpeed",      "Beam",     "Beam",      "Effects"),
    "effects fade":     ("EffectsFade",       "Beam",     "Beam",      "Effects"),
    "blade 1":          ("Blade1A",           "Shapers",  "Shapers",   "Blade"),
    "blade 2":          ("Blade2A",           "Shapers",  "Shapers",   "Blade"),
    "blade 3":          ("Blade3A",           "Shapers",  "Shapers",   "Blade"),
    "blade 4":          ("Blade4A",           "Shapers",  "Shapers",   "Blade"),
    "blade rotation":   ("ShaperRot",         "Shapers",  "Shapers",   "Blade"),
    "macro":            ("Macro",             "Control",  "Control",   "Macro"),
    "scene":            ("Macro",             "Control",  "Control",   "Macro"),
    "program":          ("Macro",             "Control",  "Control",   "Macro"),
    "function":         ("Function",          "Control",  "Control",   "Function"),
    "control":          ("Function",          "Control",  "Control",   "Function"),
    "reset":            ("Function",          "Control",  "Control",   "Function"),
    "lamp":             ("LampControl",       "Control",  "Control",   "Function"),
    "fans":             ("Function",          "Control",  "Control",   "Function"),
    "speed":            ("EffectsSpeed",      "Beam",     "Beam",      "Effects"),
    "video":            ("VideoEffect1Type",  "Control",  "Control",   "Function"),
    "media":            ("VideoEffect1Type",  "Control",  "Control",   "Function"),
}

WHEEL_ATTRS = {
    "Color1", "Color2", "Gobo1", "Gobo2", "Gobo1Pos", "Gobo2Pos",
    "Prism1", "Effects1", "Animation1", "Macro", "LampControl",
    "Function", "Shutter1", "Shutter1Strobe",
}

# Channels that are continuous (no DMX slots needed)
CONTINUOUS = {
    "Dimmer", "Dimmer Fine", "Pan", "Pan Fine", "Tilt", "Tilt Fine",
    "Red", "Green", "Blue", "White", "Amber", "Lime", "UV", "Indigo",
    "Cyan", "Magenta", "Yellow", "CTO", "CTB", "Hue", "Saturation",
    "Zoom", "Zoom Fine", "Focus", "Focus Fine", "Iris",
    "Pan Speed", "Tilt Speed", "Effects Speed", "Effects Fade",
    "Gobo Rotation", "Gobo Spin", "Gobo Index", "Prism Rotation",
    "Blade 1", "Blade 2", "Blade 3", "Blade 4", "Blade Rotation",
}

PRESETS = {
    "Shutter": [
        (0,9,"Closed"),(10,19,"Open"),
        (20,129,"Strobe Slow-Fast"),(130,139,"Open"),
        (140,189,"Pulse"),(190,199,"Open"),
        (200,249,"Random Strobe"),(250,255,"Open"),
    ],
    "Strobe": [(0,9,"Closed"),(10,19,"Open"),(20,255,"Strobe Slow-Fast")],
    "Macro": [
        (0,9,"Off"),(10,19,"Macro 1"),(20,29,"Macro 2"),
        (30,39,"Macro 3"),(40,49,"Macro 4"),(50,59,"Macro 5"),
    ],
    "Function": [
        (0,9,"No Function"),(10,19,"Reset"),
        (20,29,"Lamp On"),(30,39,"Lamp Off"),
    ],
    "Control": [
        (0,9,"No Function"),(10,19,"Reset"),
        (20,29,"Lamp On"),(30,39,"Lamp Off"),
    ],
    "Color Wheel": [
        (0,9,"Open"),(10,19,"Color 1"),(20,29,"Color 2"),
        (30,39,"Color 3"),(40,49,"Color 4"),(50,59,"Color 5"),
        (60,69,"Color 6"),(70,79,"Color 7"),(80,89,"Color 8"),
    ],
    "Colour Wheel": [
        (0,9,"Open"),(10,19,"Color 1"),(20,29,"Color 2"),
        (30,39,"Color 3"),(40,49,"Color 4"),(50,59,"Color 5"),
    ],
    "Gobo Wheel": [
        (0,9,"Open"),(10,19,"Gobo 1"),(20,29,"Gobo 2"),
        (30,39,"Gobo 3"),(40,49,"Gobo 4"),(50,59,"Gobo 5"),
        (60,69,"Gobo 6"),(70,79,"Gobo 7"),
    ],
    "Gobo 1": [
        (0,9,"Open"),(10,19,"Gobo 1"),(20,29,"Gobo 2"),
        (30,39,"Gobo 3"),(40,49,"Gobo 4"),(50,59,"Gobo 5"),
    ],
    "Gobo 2": [
        (0,9,"Open"),(10,19,"Gobo 1"),(20,29,"Gobo 2"),
        (30,39,"Gobo 3"),(40,49,"Gobo 4"),(50,59,"Gobo 5"),
    ],
    "Prism": [(0,9,"No Prism"),(10,255,"Prism")],
    "Effects": [
        (0,9,"No Effect"),(10,19,"Effect 1"),
        (20,29,"Effect 2"),(30,39,"Effect 3"),
    ],
    "Scene": [
        (0,9,"Off"),(10,19,"Scene 1"),(20,29,"Scene 2"),
        (30,39,"Scene 3"),(40,49,"Scene 4"),(50,59,"Scene 5"),
    ],
    "Program": [
        (0,9,"Off"),(10,19,"Program 1"),(20,29,"Program 2"),
        (30,39,"Program 3"),(40,49,"Program 4"),
    ],
}

CHANNEL_CATALOGUE = {
    "DIMMING": [("Dimmer",False),("Dimmer Fine",True)],
    "POSITION": [
        ("Pan",False),("Pan Fine",True),
        ("Tilt",False),("Tilt Fine",True),
        ("Pan Speed",False),("Tilt Speed",False),
    ],
    "COLOR — RGB/W": [
        ("Red",False),("Green",False),("Blue",False),
        ("White",False),("Amber",False),("Lime",False),
        ("UV",False),("Indigo",False),
    ],
    "COLOR — CMY": [("Cyan",False),("Magenta",False),("Yellow",False)],
    "COLOR — MISC": [
        ("CTO",False),("CTB",False),
        ("Hue",False),("Saturation",False),
        ("Color Wheel",False),("Color Mix",False),
    ],
    "BEAM": [
        ("Shutter",False),("Strobe",False),("Strobe Speed",False),
        ("Zoom",False),("Zoom Fine",True),
        ("Focus",False),("Focus Fine",True),
        ("Iris",False),("Frost",False),("Diffusion",False),
    ],
    "GOBO": [
        ("Gobo Wheel",False),("Gobo 1",False),("Gobo 2",False),
        ("Gobo Rotation",False),("Gobo Index",False),("Gobo Spin",False),
    ],
    "PRISM / EFFECTS": [
        ("Prism",False),("Prism Rotation",False),
        ("Effects",False),("Effects Speed",False),
        ("Effects Fade",False),("Animation",False),
    ],
    "SHAPERS": [
        ("Blade 1",False),("Blade 2",False),
        ("Blade 3",False),("Blade 4",False),
        ("Blade Rotation",False),
    ],
    "CONTROL": [
        ("Macro",False),("Scene",False),("Program",False),
        ("Function",False),("Control",False),("Reset",False),
        ("Lamp",False),("Fans",False),("Speed",False),
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

class ChannelSlot:
    def __init__(self, name, dmx_from, dmx_to,
                 physical_from=0.0, physical_to=1.0, slot_name=""):
        self.name          = name
        self.dmx_from      = dmx_from
        self.dmx_to        = dmx_to
        self.physical_from = physical_from
        self.physical_to   = physical_to
        self.slot_name     = slot_name or name

class ChannelDef:
    def __init__(self, name, is_fine_byte=False, slots=None, geometry="body"):
        self.name         = name
        self.is_fine_byte = is_fine_byte
        self.slots        = slots or []
        self.geometry     = geometry  # "body" | "cell" | "virtual"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def resolve_attr(raw):
    clean = raw.lower().strip()
    if clean in ATTR_MAP:
        return ATTR_MAP[clean]
    for key, val in ATTR_MAP.items():
        if key in clean:
            return val
    safe = re.sub(r'[^A-Za-z0-9_]', '_', raw.strip()) or "Custom"
    return (safe, "Control", "Control", safe)

def is_fine(name):
    return any(w in name.lower()
               for w in ["fine", " lsb", "16-bit", "16bit", "low byte"])

def _safe(text, fallback="Ch"):
    s = text.strip()
    for old, new in [("°","deg"),("%","pct"),("/","_"),(".","_"),
                     (":","_"),(";","_")]:
        s = s.replace(old, new)
    s = re.sub(r'[^A-Za-z0-9_ \-]', '', s)
    s = re.sub(r'[ _]+', '_', s).strip('_')
    if not s or s[0].isdigit():
        s = fallback + "_" + s
    return s or fallback

def _guid():
    raw = uuid.uuid4().hex.upper()
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"

def _new_channel_id():
    return uuid.uuid4().hex[:8]

def make_channel_entry(name, fine=False, geometry="body"):
    return {"id": _new_channel_id(), "name": name,
            "is_fine": fine, "slots": [], "geometry": geometry}

def make_slot_entry(dmx_from=0, dmx_to=10, name=""):
    return {"dmx_from": dmx_from, "dmx_to": dmx_to, "name": name}

def _ch_list_to_defs(ch_list):
    """Convert a list of channel dicts to ChannelDef objects."""
    defs = []
    for ch in ch_list:
        slots = [
            ChannelSlot(
                name=s["name"],
                dmx_from=int(s["dmx_from"]),
                dmx_to=int(s["dmx_to"]),
                physical_from=round(int(s["dmx_from"]) / 255, 6),
                physical_to=round(int(s["dmx_to"]) / 255, 6),
                slot_name=s["name"],
            )
            for s in ch.get("slots", [])
            if s.get("name", "").strip()
        ]
        defs.append(ChannelDef(
            name=ch["name"],
            is_fine_byte=ch.get("is_fine", False),
            slots=slots,
        ))
    return defs


def channel_defs_from_mode(mode):
    """Returns (body_defs, cell_defs) — two independent ChannelDef lists."""
    # Backwards compat: old single channel_list treated as body
    if "body_channels" not in mode and "cell_channels" not in mode:
        body = _ch_list_to_defs(mode.get("channel_list", []))
        return body, []
    body = _ch_list_to_defs(mode.get("body_channels", []))
    cell = _ch_list_to_defs(mode.get("cell_channels", []))
    return body, cell


# ══════════════════════════════════════════════════════════════════════════════
#  GDTF XML BUILDER
#  single-geometry (cell_count=1) or multi-cell pixel bar (cell_count>=2)
#  DMX slots -> ChannelFunction (full range) + ChannelSet per slot
# ══════════════════════════════════════════════════════════════════════════════

def _emit_one_channel(chs_el, ch, safe_mode, wheel_registry,
                      geometry_name, offset, virtual=False):
    """
    Emit a single DMXChannel element.
    virtual=True  -> Offset="None"  (no DMX address — MA3 virtual dimmer)
    Returns (ch_el, offset_used) where offset_used is the address consumed
    (None for virtual channels).
    """
    attr, fg, feat, ag = resolve_attr(ch.name)
    safe_ch    = _safe(ch.name, f"Ch{offset if not virtual else 'V'}")
    cf_name    = attr
    offset_str = "None" if virtual else str(offset)
    initial_fn = f"{safe_mode}.{safe_ch}.{attr}.{cf_name}"

    if ch.slots:
        wname = wheel_registry.get(attr, "")
        ch_el = ET.SubElement(chs_el, "DMXChannel",
            DMXBreak="1", Offset=offset_str,
            Default="0/1", Highlight="255/1",
            Geometry=geometry_name, InitialFunction=initial_fn)
        log_el = ET.SubElement(ch_el, "LogicalChannel",
            Attribute=attr, Snap="Yes",
            Master="None", MibFade="0", DMXChangeTimeLimit="0")
        cf_kw = dict(
            Name=cf_name, Attribute=attr,
            OriginalAttribute=_safe(ch.name),
            DMXFrom="0/1", Default="0/1",
            PhysicalFrom="0.000000", PhysicalTo="1.000000",
            RealFade="0", RealAcceleration="0", WheelSlotIndex="0",
        )
        if wname:
            cf_kw["Wheel"] = wname
        cf_el = ET.SubElement(log_el, "ChannelFunction", **cf_kw)
        for slot_idx, slot in enumerate(ch.slots):
            cs_kw = dict(
                Name=_safe(slot.name, f"Set{slot_idx+1}"),
                DMXFrom=f"{slot.dmx_from}/1",
                PhysicalFrom=f"{slot.physical_from:.6f}",
                PhysicalTo=f"{slot.physical_to:.6f}",
            )
            if wname:
                cs_kw["WheelSlotIndex"] = str(slot_idx + 1)
            ET.SubElement(cf_el, "ChannelSet", **cs_kw)
    else:
        ch_el = ET.SubElement(chs_el, "DMXChannel",
            DMXBreak="1", Offset=offset_str,
            Default="0/1", Highlight="255/1",
            Geometry=geometry_name, InitialFunction=initial_fn)
        log_el = ET.SubElement(ch_el, "LogicalChannel",
            Attribute=attr, Snap="No",
            Master="None", MibFade="0", DMXChangeTimeLimit="0")
        ET.SubElement(log_el, "ChannelFunction",
            Name=cf_name, Attribute=attr,
            OriginalAttribute=_safe(ch.name),
            DMXFrom="0/1", Default="0/1",
            PhysicalFrom="0.000000", PhysicalTo="1.000000",
            RealFade="0", RealAcceleration="0", WheelSlotIndex="0")

    return ch_el


def _emit_channels_for_geometry(chs_el, channels, safe_mode,
                                wheel_registry, geometry_name, start_offset):
    """Emit a list of ChannelDef objects to geometry_name. Returns next offset."""
    offset = start_offset
    prev_ch_el = None
    prev_offset_start = None

    for ch in channels:
        if not ch.name.strip():
            continue
        if ch.is_fine_byte:
            if prev_ch_el is not None:
                prev_ch_el.set("Offset", f"{prev_offset_start},{offset}")
            offset += 1
            prev_ch_el = None
            continue

        virtual = (getattr(ch, "geometry", "body") == "virtual")
        ch_el = _emit_one_channel(chs_el, ch, safe_mode, wheel_registry,
                                  geometry_name, offset, virtual=virtual)
        if not virtual:
            prev_ch_el = ch_el
            prev_offset_start = offset
            offset += 1
        # virtual channels don't advance offset and don't pair with fine bytes

    return offset


def build_gdtf(fixture_name, manufacturer, modes_dict, cell_count=1):
    """
    modes_dict values are (body_defs, cell_defs) tuples.
    cell_count=1  -> single Body geometry, body_defs only (par, wash, strobe)
    cell_count>=2 -> pixel bar: body_defs to Body once, cell_defs to Cell_N × N
    MA3 treats each Cell_N as a pixel-mappable element with independent wheels.
    """
    multi_cell = cell_count >= 2
    root = ET.Element("GDTF", DataVersion="1.1")

    safe_name  = _safe(fixture_name, "Fixture")
    safe_short = re.sub(r'[^A-Z0-9]', '', safe_name.upper())[:8] or "FIXTURE"
    safe_mfr   = _safe(manufacturer, "Generic")

    ft = ET.SubElement(root, "FixtureType",
        Name=safe_name, ShortName=safe_short, LongName=safe_name,
        Manufacturer=safe_mfr, Description="Generated by GDTF Builder",
        FixtureTypeID=_guid(), Thumbnail="", RefFT="", CanHaveChildren="No")

    # Collect used attributes from both body and cell channel lists
    used_attrs = {}
    for body_chs, cell_chs in modes_dict.values():
        for ch in body_chs + cell_chs:
            if not ch.is_fine_byte and ch.name.strip():
                attr, fg, feat, ag = resolve_attr(ch.name)
                used_attrs[attr] = (fg, feat, ag)

    # AttributeDefinitions
    attr_defs = ET.SubElement(ft, "AttributeDefinitions")
    ag_xml = ET.SubElement(attr_defs, "ActivationGroups")
    ag_seen = set()
    for _, (fg, feat, ag) in used_attrs.items():
        if ag not in ag_seen:
            ET.SubElement(ag_xml, "ActivationGroup", Name=ag)
            ag_seen.add(ag)
    fg_xml = ET.SubElement(attr_defs, "FeatureGroups")
    fg_used = {}
    for _, (fg, feat, ag) in used_attrs.items():
        fg_used.setdefault(fg, set()).add(feat)
    for fg_name, feats in fg_used.items():
        fg_el = ET.SubElement(fg_xml, "FeatureGroup", Name=fg_name, Pretty=fg_name)
        for f in sorted(feats):
            ET.SubElement(fg_el, "Feature", Name=f)
    attrs_xml = ET.SubElement(attr_defs, "Attributes")
    for attr, (fg, feat, ag) in used_attrs.items():
        ET.SubElement(attrs_xml, "Attribute",
            Name=attr, Pretty=attr, ActivationGroup=ag,
            Feature=f"{fg}.{feat}", PhysicalUnit="None",
            Color="0.3127,0.3290,100.000000")

    # Wheels — body and cell are independent, so collect separately.
    # Each geometry can have its own wheel with the same attribute name.
    # We prefix cell wheels with "Cell_" to avoid name clashes with body wheels.
    body_wheel_registry = {}
    cell_wheel_registry = {}
    for body_chs, cell_chs in modes_dict.values():
        for ch in body_chs:
            if ch.is_fine_byte or not ch.slots:
                continue
            attr, *_ = resolve_attr(ch.name)
            if attr not in WHEEL_ATTRS or attr in body_wheel_registry:
                continue
            body_wheel_registry[attr] = _safe(ch.name, attr)
        for ch in cell_chs:
            if ch.is_fine_byte or not ch.slots:
                continue
            attr, *_ = resolve_attr(ch.name)
            if attr not in WHEEL_ATTRS or attr in cell_wheel_registry:
                continue
            cell_wheel_registry[attr] = "Cell_" + _safe(ch.name, attr)

    # Combined registry for emit function — cell takes precedence if same attr
    wheel_registry = {**body_wheel_registry, **cell_wheel_registry}

    wheels_el = ET.SubElement(ft, "Wheels")

    def _emit_wheel(ch_list, registry):
        for ch in ch_list:
            if ch.is_fine_byte or not ch.slots:
                continue
            attr, *_ = resolve_attr(ch.name)
            wname = registry.get(attr)
            if not wname:
                continue
            if wheels_el.find(f"Wheel[@Name='{wname}']") is not None:
                continue
            wheel_el = ET.SubElement(wheels_el, "Wheel", Name=wname)
            ET.SubElement(wheel_el, "Slot", Name="Open",
                          Color="0.3127,0.3290,100.000000", MediaFileName="")
            for slot in ch.slots:
                ET.SubElement(wheel_el, "Slot",
                              Name=_safe(slot.slot_name, "Slot"),
                              Color="0.3127,0.3290,100.000000", MediaFileName="")

    for body_chs, cell_chs in modes_dict.values():
        _emit_wheel(body_chs, body_wheel_registry)
        _emit_wheel(cell_chs, cell_wheel_registry)

    # Physical / Models
    phys = ET.SubElement(ft, "PhysicalDescriptions")
    ET.SubElement(phys, "Emitters")
    ET.SubElement(phys, "Filters")
    ET.SubElement(phys, "DMXProfiles")
    ET.SubElement(phys, "CRIs")
    ET.SubElement(ft, "Models")

    # Geometries
    IDENTITY = "1,0,0,0 0,1,0,0 0,0,1,0 0,0,0,1"
    geos = ET.SubElement(ft, "Geometries")
    if not multi_cell:
        ET.SubElement(geos, "Geometry", Name="Body", Model="", Position=IDENTITY)
    else:
        # Body is the root (non-pixel control channels live here if any)
        body_el = ET.SubElement(geos, "Geometry", Name="Body",
                                Model="", Position=IDENTITY)
        # N GeometryReferences spaced 0.1m apart along X
        for n in range(1, cell_count + 1):
            x = (n - 1) * 0.1
            pos = f"1,0,0,0 0,1,0,0 0,0,1,0 {x:.3f},0,0,1"
            ET.SubElement(body_el, "GeometryReference",
                          Name=f"Cell_{n}", Position=pos, Geometry="Cell")
        # Cell template geometry at root level
        ET.SubElement(geos, "Geometry", Name="Cell", Model="", Position=IDENTITY)

    # DMX Modes
    dmx_modes_el = ET.SubElement(ft, "DMXModes")
    for mode_name, (body_chs, cell_chs) in modes_dict.items():
        safe_mode = _safe(mode_name, "Mode")
        mode_el = ET.SubElement(dmx_modes_el, "DMXMode",
                                Name=safe_mode, Geometry="Body")
        chs_el = ET.SubElement(mode_el, "DMXChannels")

        if not multi_cell:
            # Single geometry — body channels only, all go to Body
            _emit_channels_for_geometry(
                chs_el, body_chs, safe_mode,
                body_wheel_registry, "Body", start_offset=1)
        else:
            # Body channels emitted once to Body geometry
            next_offset = _emit_channels_for_geometry(
                chs_el, body_chs, safe_mode,
                body_wheel_registry, "Body", start_offset=1)
            # Cell channels repeated once per cell, each to its own Cell_N geometry
            for n in range(1, cell_count + 1):
                next_offset = _emit_channels_for_geometry(
                    chs_el, cell_chs, safe_mode,
                    cell_wheel_registry, f"Cell_{n}",
                    start_offset=next_offset)

        ET.SubElement(mode_el, "Relations")
        ET.SubElement(mode_el, "FTMacros")

    revisions = ET.SubElement(ft, "Revisions")
    ET.SubElement(revisions, "Revision",
                  UserID="0", Date="2024-01-01T00:00:00",
                  Text="Created by GDTF Builder", ModifiedBy="GDTFBuilder")
    ET.SubElement(ft, "FTPresets")
    ET.SubElement(ft, "FTRDMInfo")

    raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
    pretty = minidom.parseString(
        f'<?xml version="1.0" encoding="UTF-8"?>{raw}'
    ).toprettyxml(indent="  ", encoding=None)
    return pretty.replace('<?xml version="1.0" ?>',
                          '<?xml version="1.0" encoding="UTF-8"?>')


def create_gdtf_package(xml_content):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        z.writestr("description.xml", xml_content.encode("utf-8"))
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
#  WHEEL REFERENCE VALIDATOR
#  Every Wheel= in a ChannelFunction must name a Wheel that exists.
#  MA3 silently drops channels with broken wheel references on import.
# ══════════════════════════════════════════════════════════════════════════════

def validate_wheel_references(xml_str):
    errors = []
    try:
        root = ET.fromstring(xml_str.encode("utf-8"))
        ft   = root.find("FixtureType")
        if ft is None:
            return ["Could not find FixtureType element"]
        defined_wheels = {w.get("Name") for w in ft.findall(".//Wheels/Wheel")}
        for cf in ft.findall(".//ChannelFunction"):
            wref = cf.get("Wheel")
            if wref and wref not in defined_wheels:
                ch_name = cf.get("OriginalAttribute", "?")
                errors.append(
                    f"Channel '{ch_name}': references Wheel '{wref}' "
                    f"which is not defined. Defined: {sorted(defined_wheels) or 'none'}"
                )
    except Exception as e:
        errors.append(f"Validation parse error: {e}")
    return errors


# ══════════════════════════════════════════════════════════════════════════════
#  STREAMLIT PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="GDTF Builder", page_icon="💡",
                   layout="wide", initial_sidebar_state="collapsed")

# Force dark before Streamlit renders — kills white flash
st.markdown("""
<style>
html,body,#root,#root>div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
[data-testid="stMain"],
.main,.block-container,section.main {
    background-color:#0A0A0A !important;
    background:#0A0A0A !important;
}
[data-testid="stHeader"] {
    background-color:#0A0A0A !important;
    border-bottom:1px solid #3A3A3A !important;
}
[data-testid="stToolbar"] { background:#0A0A0A !important; }
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#0A0A0A; }
::-webkit-scrollbar-thumb { background:#3A3A3A; border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#E8A000; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;500;600&display=swap');

:root {
    --ma-black:    #0A0A0A;
    --ma-panel:    #1A1A1A;
    --ma-border:   #3A3A3A;
    --ma-amber:    #E8A000;
    --ma-amber-dk: #A06800;
    --ma-text:     #EBEBEB;
    --ma-muted:    #AAAAAA;
    --ma-green:    #00E000;
    --ma-red:      #FF5555;
    --ma-blue:     #4AB0FF;
}

html,body,[class*="css"] {
    font-family:'Barlow',sans-serif;
    background:var(--ma-black) !important;
    color:var(--ma-text);
}
h1,h2,h3,h4 {
    font-family:'Share Tech Mono',monospace;
    letter-spacing:0.04em;
    color:var(--ma-amber);
}
/* Mobile-friendly max-width and padding */
.block-container {
    padding-top:1rem !important;
    padding-left:1rem !important;
    padding-right:1rem !important;
    max-width:900px;
}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background:var(--ma-panel) !important;
    border:1px solid var(--ma-border) !important;
    border-radius:3px !important;
    color:var(--ma-text) !important;
    font-family:'Share Tech Mono',monospace !important;
    font-size:0.9rem !important;
    /* Larger tap target on mobile */
    min-height:2.4rem !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color:var(--ma-amber) !important;
    box-shadow:0 0 0 2px rgba(232,160,0,0.2) !important;
}
div[data-testid="stNumberInput"] input {
    background:var(--ma-panel) !important;
    border:1px solid var(--ma-border) !important;
    color:var(--ma-text) !important;
    font-family:'Share Tech Mono',monospace !important;
    min-height:2.4rem !important;
}

label, .stRadio label, div[data-testid="stWidgetLabel"] {
    color:#BBBBBB !important;
    font-size:0.75rem !important;
    text-transform:uppercase;
    letter-spacing:0.08em;
}

/* ── Buttons — larger tap targets on mobile ─────────────────────────────── */
.stButton>button[kind="primary"] {
    background:var(--ma-amber);
    border:1px solid var(--ma-amber);
    border-bottom:2px solid var(--ma-amber-dk);
    border-radius:3px; color:#000;
    font-family:'Share Tech Mono',monospace;
    font-size:0.85rem; font-weight:700;
    letter-spacing:0.08em;
    padding:0.65rem 1.5rem;
    min-height:2.8rem;
    text-transform:uppercase;
    width:100%;
    transition:background .15s;
}
.stButton>button[kind="primary"]:hover { background:#FFB800; }

.stButton>button:not([kind="primary"]) {
    background:var(--ma-panel);
    border:1px solid var(--ma-border);
    border-bottom:2px solid #111;
    border-radius:3px; color:#CCCCCC;
    font-family:'Share Tech Mono',monospace;
    font-size:0.8rem; letter-spacing:0.04em;
    text-transform:uppercase;
    min-height:2.6rem;
    transition:border-color .15s,color .15s;
}
.stButton>button:not([kind="primary"]):hover {
    border-color:var(--ma-amber);
    color:var(--ma-amber);
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.card {
    background:var(--ma-panel);
    border:1px solid var(--ma-border);
    border-top:2px solid var(--ma-amber);
    border-radius:3px;
    padding:0.85rem 1rem;
    margin-bottom:1rem;
}

/* ── Badges ─────────────────────────────────────────────────────────────── */
.badge {
    display:inline-block; border-radius:2px;
    padding:3px 8px;
    font-family:'Share Tech Mono',monospace;
    font-size:0.7rem; margin:2px; border:1px solid;
    text-transform:uppercase; letter-spacing:0.04em;
}
.b-ok   { color:var(--ma-amber); border-color:#E8A00066; background:#E8A00020; }
.b-fine { color:var(--ma-blue);  border-color:#4AB0FF66; background:#4AB0FF20; }
.b-slot { color:var(--ma-green); border-color:#00E00066; background:#00E00020; }
.b-unk  { color:var(--ma-red);   border-color:#FF555566; background:#FF555520; }

/* ── Info / warn ────────────────────────────────────────────────────────── */
.info-box {
    background:#141414; border-left:3px solid var(--ma-amber);
    border-radius:0 3px 3px 0; padding:0.7rem 1rem;
    font-size:0.82rem; color:#BBBBBB; margin:0.5rem 0;
}
.warn-box {
    background:#1A1200; border-left:3px solid #D07000;
    border-radius:0 3px 3px 0; padding:0.7rem 1rem;
    font-size:0.82rem; color:#D09040; margin:0.5rem 0;
}

/* ── Channel row ────────────────────────────────────────────────────────── */
.ch-num {
    color:var(--ma-amber);
    font-family:'Share Tech Mono',monospace;
    font-size:0.82rem;
    margin-top:0.6rem;
    text-align:right;
}

/* ── Slot table ─────────────────────────────────────────────────────────── */
.slot-row {
    display:flex; gap:8px; align-items:center;
    padding:4px 0; border-bottom:1px solid var(--ma-border);
    font-size:0.78rem; font-family:'Share Tech Mono',monospace;
}
.slot-dmx  { color:var(--ma-amber); width:90px; flex-shrink:0; }
.slot-name { color:#DDDDDD; flex:1; }

/* ── Expanders ──────────────────────────────────────────────────────────── */
details summary {
    font-family:'Share Tech Mono',monospace !important;
    font-size:0.8rem !important; color:#BBBBBB !important;
    text-transform:uppercase; letter-spacing:0.06em;
}
details summary:hover { color:var(--ma-amber) !important; }

hr { border-color:#3A3A3A !important; }

/* ── Mobile tweaks ──────────────────────────────────────────────────────── */
@media (max-width:640px) {
    .block-container {
        padding-left:0.5rem !important;
        padding-right:0.5rem !important;
    }
    h1 { font-size:1.4rem !important; }
    .stButton>button { min-height:3rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.title("GDTF BUILDER")
st.markdown(
    "<p style='color:#BBBBBB;font-size:0.75rem;margin-top:-0.8rem;"
    "font-family:Share Tech Mono,monospace;letter-spacing:0.1em'>"
    "GDTF 1.1 &nbsp;·&nbsp; MA3 CHANNEL SETS &amp; WHEELS &nbsp;·&nbsp; "
    "VECTORWORKS &nbsp;·&nbsp; CAPTURE &nbsp;·&nbsp; ONYX</p>",
    unsafe_allow_html=True
)
st.divider()

# ── Fixture metadata ──────────────────────────────────────────────────────────
st.markdown(
    "<p style='color:#BBBBBB;font-family:Share Tech Mono,monospace;"
    "font-size:0.72rem;letter-spacing:0.1em;margin-bottom:0.2rem'>"
    "FIXTURE INFO</p>",
    unsafe_allow_html=True
)
fi1, fi2 = st.columns(2)
with fi1:
    fixture_name = st.text_input(
        "MODEL NAME",
        value=st.session_state.get("fixture_name", "Generic LED Par")
    )
    st.session_state["fixture_name"] = fixture_name
with fi2:
    manufacturer = st.text_input(
        "MANUFACTURER",
        value=st.session_state.get("manufacturer", "Generic")
    )
    st.session_state["manufacturer"] = manufacturer

# ── Pixel bar / multi-cell config ─────────────────────────────────────────────
with st.expander("⬡ MULTI-CELL / PIXEL BAR — expand to configure"):
    st.markdown(
        '''<div class="info-box">
        <b>Single fixture</b> — leave at 1 cell for a standard par, wash, or strobe.<br>
        <b>Pixel bar / multi-head</b> — set cell count to the number of individually
        addressable pixels or heads. Each cell gets its own copy of the channel list
        in the DMX mode. MA3 enables pixel mapping automatically for multi-cell fixtures.
        </div>''',
        unsafe_allow_html=True
    )
    pc1, pc2 = st.columns([1, 2])
    with pc1:
        cell_count = st.number_input(
            "NUMBER OF CELLS",
            min_value=1, max_value=100,
            value=st.session_state.get("cell_count", 1),
            help="1 = standard fixture. 2+ = pixel bar / multi-instance."
        )
        st.session_state["cell_count"] = int(cell_count)
    with pc2:
        n = int(st.session_state.get("cell_count", 1))
        ch_per_cell = sum(
            1 for m in st.session_state.get("modes", [{}])[:1]
            for ch in m.get("channel_list", [])
            if not ch.get("is_fine", False)
        )
        total_dmx = n * ch_per_cell if n > 1 else ch_per_cell
        if n == 1:
            st.markdown(
                '<p style="color:#AAAAAA;font-size:0.82rem;margin-top:1.8rem">' +
                'Single geometry — standard fixture.</p>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<p style="color:var(--ma-amber);font-family:Share Tech Mono,' +
                f'monospace;font-size:0.82rem;margin-top:1.8rem">' +
                f'{n} cells · ~{total_dmx} DMX addresses per mode · ' +
                f'MA3 pixel mapping enabled</p>',
                unsafe_allow_html=True
            )

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════

if "modes" not in st.session_state:
    st.session_state.modes = [{
        "name": "Standard Mode",
        "body_channels": [
            make_channel_entry("Dimmer"),
            make_channel_entry("Dimmer Fine", True),
            make_channel_entry("Strobe"),
            make_channel_entry("Macro"),
        ],
        "cell_channels": [
            make_channel_entry("Red"),
            make_channel_entry("Green"),
            make_channel_entry("Blue"),
        ],
    }]

def _fresh_ids(ch_list):
    for ch in ch_list:
        ch["id"] = _new_channel_id()

def add_mode():
    st.session_state.modes.append({
        "name": f"Mode {len(st.session_state.modes)+1}",
        "body_channels": [make_channel_entry("Dimmer")],
        "cell_channels": [make_channel_entry("Red"),
                          make_channel_entry("Green"),
                          make_channel_entry("Blue")],
    })

def copy_mode(i):
    src   = st.session_state.modes[i]
    clone = copy.deepcopy(src)
    _fresh_ids(clone.get("body_channels", []))
    _fresh_ids(clone.get("cell_channels", []))
    clone["name"] = src["name"] + " (Copy)"
    st.session_state.modes.insert(i + 1, clone)

def remove_mode(i):
    if len(st.session_state.modes) > 1:
        st.session_state.modes.pop(i)


# ══════════════════════════════════════════════════════════════════════════════
#  CHANNEL LIST + PICKER  — reusable render function
# ══════════════════════════════════════════════════════════════════════════════

def render_channel_list(ch_list, tab_key, mode_idx):
    """
    Render a channel list (body or cell) with its inline slot editor and picker.
    tab_key  — unique prefix string to avoid widget key collisions between tabs.
    """
    # ── Ensure stable IDs ──────────────────────────────────────────────────────
    for ch in ch_list:
        if "id" not in ch:
            ch["id"] = _new_channel_id()

    n_ch     = len(ch_list)
    ch_label = (
        f"{n_ch} channel{'s' if n_ch != 1 else ''} — DMX order"
        if n_ch > 0 else "empty — add channels below"
    )

    ch_to_delete = None
    ch_to_move   = None

    with st.expander(ch_label, expanded=True):

        # Virtual dimmer shortcut for cell tab
        if tab_key.endswith("_cell"):
            if st.button("＋ Virtual Dimmer",
                         key=f"vdim_{tab_key}",
                         help="Adds a Dimmer with Offset=None — no DMX address. "
                              "MA3 uses it as per-cell intensity for pixel mapping."):
                ch_list.append(make_channel_entry("Virtual Dimmer"))
                st.rerun()

        if not ch_list:
            st.markdown(
                '<p style="color:#AAAAAA;font-size:0.85rem;padding:0.4rem 0">'
                'No channels yet — use the picker below.</p>',
                unsafe_allow_html=True
            )

        for ci, ch in enumerate(ch_list):
            ch_id = ch["id"]
            attr, *_ = resolve_attr(ch["name"])
            known = any(k in ch["name"].lower() for k in ATTR_MAP)
            fine  = ch.get("is_fine", False)
            # Virtual dimmer = any channel named "virtual dimmer"
            is_virtual = "virtual" in ch["name"].lower() and "dimmer" in ch["name"].lower()

            if is_virtual:
                badge = '<span class="badge b-fine">VIRT</span>'
            elif fine:
                badge = '<span class="badge b-fine">FINE</span>'
            else:
                badge = f'<span class="badge {"b-ok" if known else "b-unk"}">{attr}</span>'

            r1, r2, r3, r4, r5, r6 = st.columns([0.4, 2.5, 1.2, 0.35, 0.35, 0.35])

            with r1:
                num = "V" if is_virtual else str(ci + 1)
                st.markdown(f'<p class="ch-num">{num}</p>', unsafe_allow_html=True)
            with r2:
                new_name = st.text_input(
                    "ch", value=ch["name"],
                    label_visibility="collapsed",
                    key=f"chname_{tab_key}_{ch_id}"
                )
                if new_name != ch["name"]:
                    ch["name"] = new_name
            with r3:
                st.markdown(f'<div style="margin-top:0.5rem">{badge}</div>',
                            unsafe_allow_html=True)
            with r4:
                if st.button("▲", key=f"up_{tab_key}_{ch_id}",
                             disabled=ci == 0, help="Move up"):
                    ch_to_move = (ci, -1)
            with r5:
                if st.button("▼", key=f"dn_{tab_key}_{ch_id}",
                             disabled=ci == len(ch_list) - 1, help="Move down"):
                    ch_to_move = (ci, 1)
            with r6:
                if st.button("✕", key=f"del_{tab_key}_{ch_id}",
                             help="Remove channel"):
                    ch_to_delete = ci

            # ── DMX Slot / Channel Set editor ─────────────────────────────────
            show_slots = (
                not fine and not is_virtual and
                ch["name"] not in CONTINUOUS and known
            )
            if show_slots:
                slots = ch.setdefault("slots", [])
                n     = len(slots)
                s_label = (
                    f"  ↳ {n} channel set{'s' if n != 1 else ''} (MA3 snap positions)"
                    if n > 0 else "  ↳ No channel sets — tap to add (optional)"
                )
                with st.expander(s_label, expanded=n > 0):
                    if slots:
                        hh1, hh2, hh3, _ = st.columns([1,1,2,0.4])
                        for lbl, col in zip(["FROM","TO","LABEL (MA3 CHANNEL SET)"],
                                            [hh1, hh2, hh3]):
                            with col:
                                st.markdown(
                                    f'<p style="color:#888;font-size:0.68rem;'
                                    f'font-family:Share Tech Mono,monospace;'
                                    f'text-transform:uppercase;letter-spacing:0.06em;'
                                    f'margin-bottom:0.2rem">{lbl}</p>',
                                    unsafe_allow_html=True)

                    slot_to_delete = None
                    for si, slot in enumerate(slots):
                        sc1, sc2, sc3, sc4 = st.columns([1,1,2,0.4])
                        with sc1:
                            slot["dmx_from"] = st.number_input(
                                "From", min_value=0, max_value=255,
                                value=int(slot["dmx_from"]),
                                key=f"sf_{tab_key}_{ch_id}_{si}",
                                label_visibility="collapsed")
                        with sc2:
                            slot["dmx_to"] = st.number_input(
                                "To", min_value=0, max_value=255,
                                value=int(slot["dmx_to"]),
                                key=f"st_{tab_key}_{ch_id}_{si}",
                                label_visibility="collapsed")
                        with sc3:
                            slot["name"] = st.text_input(
                                "Label", value=slot["name"],
                                placeholder="e.g. Open / Gobo 3 / Slow CW",
                                key=f"sn_{tab_key}_{ch_id}_{si}",
                                label_visibility="collapsed")
                        with sc4:
                            if st.button("✕", key=f"sdel_{tab_key}_{ch_id}_{si}"):
                                slot_to_delete = si

                    if slot_to_delete is not None:
                        slots.pop(slot_to_delete)
                        st.rerun()

                    next_from = slots[-1]["dmx_to"] + 1 if slots else 0
                    next_to   = min(next_from + 10, 255)
                    if st.button(f"＋ Add channel set  (next: {next_from}–{next_to})",
                                 key=f"sadd_{tab_key}_{ch_id}",
                                 use_container_width=True):
                        slots.append(make_slot_entry(next_from, next_to, ""))
                        st.rerun()

                    preset_match = next(
                        (v for k, v in PRESETS.items()
                         if k.lower() in ch["name"].lower()), None)
                    if preset_match and not slots:
                        if st.button("⚡ Quick-fill standard channel sets",
                                     key=f"preset_{tab_key}_{ch_id}",
                                     use_container_width=True):
                            for pf, pt, pn in preset_match:
                                slots.append(make_slot_entry(pf, pt, pn))
                            st.rerun()

                    if slots:
                        st.markdown(
                            '<p style="color:#777;font-size:0.72rem;'
                            'font-family:Share Tech Mono,monospace;margin-top:0.4rem">'
                            '⟶ Named snap positions on MA3 encoders / channel sets column.</p>',
                            unsafe_allow_html=True)

    # Apply moves/deletes outside the expander
    if ch_to_delete is not None:
        ch_list.pop(ch_to_delete)
        st.rerun()
    if ch_to_move is not None:
        i, d = ch_to_move
        j = i + d
        if 0 <= j < len(ch_list):
            ch_list[i], ch_list[j] = ch_list[j], ch_list[i]
        st.rerun()

    # ── Channel Picker ─────────────────────────────────────────────────────────
    with st.expander("＋ ADD CHANNELS — tap a group to browse"):
        for group_name, group_channels in CHANNEL_CATALOGUE.items():
            with st.expander(group_name):
                gcols = st.columns(2)
                for ci2, (ch_name, ch_fine) in enumerate(group_channels):
                    with gcols[ci2 % 2]:
                        already = any(c["name"].lower() == ch_name.lower()
                                      for c in ch_list)
                        label = f"✓ {ch_name}" if already else f"＋ {ch_name}"
                        if st.button(label,
                                     key=f"pick_{tab_key}_{group_name}_{ch_name}",
                                     use_container_width=True):
                            if not already:
                                ch_list.append(make_channel_entry(ch_name, ch_fine))
                                st.rerun()

        st.markdown(
            '<p style="color:#BBBBBB;font-family:Share Tech Mono,monospace;'
            'font-size:0.72rem;letter-spacing:0.08em;margin:0.8rem 0 0.3rem">'
            'CUSTOM CHANNEL NAME</p>',
            unsafe_allow_html=True)
        cc1, cc2 = st.columns([4, 1])
        with cc1:
            custom_name = st.text_input(
                "Custom", label_visibility="collapsed",
                placeholder="e.g. Pixel Row 1 / CTC / Virtual Dimmer",
                key=f"custom_{tab_key}")
        with cc2:
            if st.button("ADD", key=f"custom_add_{tab_key}",
                         use_container_width=True):
                if custom_name.strip():
                    ch_list.append(make_channel_entry(
                        custom_name.strip(), is_fine(custom_name)))
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PER-MODE RENDERING
# ══════════════════════════════════════════════════════════════════════════════

for mode_idx, mode in enumerate(st.session_state.modes):

    # ── Backwards compat: migrate old channel_list to body_channels ───────────
    if "body_channels" not in mode and "cell_channels" not in mode:
        old = mode.get("channel_list", [])
        mode["body_channels"] = old
        mode["cell_channels"] = []
        mode.pop("channel_list", None)

    body_list = mode.setdefault("body_channels", [])
    cell_list = mode.setdefault("cell_channels", [])
    is_mc     = int(st.session_state.get("cell_count", 1)) >= 2

    st.markdown('<div class="card">', unsafe_allow_html=True)

    # ── Mode header ───────────────────────────────────────────────────────────
    hc1, hc2, hc3, hc4 = st.columns([3, 1, 1, 1])
    with hc1:
        mode["name"] = st.text_input(
            "MODE NAME", value=mode["name"], key=f"mname_{mode_idx}")
    with hc2:
        st.write(""); st.write("")
        if st.button("⧉ Copy", key=f"copy_{mode_idx}", help="Duplicate this mode"):
            copy_mode(mode_idx)
            st.rerun()
    with hc3:
        st.write(""); st.write("")
        if is_mc:
            n_body = sum(1 for c in body_list if not c.get("is_fine"))
            n_cell = sum(1 for c in cell_list if not c.get("is_fine")
                         and "virtual" not in c["name"].lower())
            n_virt = sum(1 for c in cell_list
                         if "virtual" in c["name"].lower())
            cells  = int(st.session_state.get("cell_count", 1))
            total  = n_body + n_cell * cells
            st.markdown(
                f'<p style="color:var(--ma-amber);font-family:Share Tech Mono,'
                f'monospace;font-size:0.75rem;margin-top:0.5rem;line-height:1.4">'
                f'{total} DMX<br>'
                f'<span style="font-size:0.65rem;color:#AAAAAA">'
                f'B:{n_body} C:{n_cell}×{cells} V:{n_virt}</span></p>',
                unsafe_allow_html=True)
        else:
            n_ch = sum(1 for c in body_list if not c.get("is_fine"))
            st.markdown(
                f'<p style="color:var(--ma-amber);font-family:Share Tech Mono,'
                f'monospace;font-size:0.82rem;margin-top:0.55rem">'
                f'{n_ch} CH</p>',
                unsafe_allow_html=True)
    with hc4:
        st.write(""); st.write("")
        if st.button("🗑", key=f"rm_{mode_idx}",
                     disabled=len(st.session_state.modes) == 1,
                     help="Remove mode"):
            remove_mode(mode_idx)
            st.rerun()

    st.divider()

    # ── Body / Cell tabs (tabs only shown in multi-cell mode) ─────────────────
    if is_mc:
        tab_body, tab_cell = st.tabs([
            f"🟡 BODY  ({len(body_list)} ch)",
            f"🟢 CELL  ({len(cell_list)} ch)  × {int(st.session_state.get('cell_count',1))} cells",
        ])
        with tab_body:
            st.markdown(
                '<p style="color:#AAAAAA;font-size:0.75rem;margin-bottom:0.5rem">'
                'Channels emitted <b>once</b> to the Body geometry — '
                'master dimmer, strobe, color temp, macros, etc.</p>',
                unsafe_allow_html=True)
            render_channel_list(body_list, f"m{mode_idx}_body", mode_idx)
        with tab_cell:
            st.markdown(
                '<p style="color:#AAAAAA;font-size:0.75rem;margin-bottom:0.5rem">'
                'Channels repeated for <b>every cell</b> — RGB, RGBW, etc. '
                'Each cell gets its own independent wheels and channel sets.</p>',
                unsafe_allow_html=True)
            render_channel_list(cell_list, f"m{mode_idx}_cell", mode_idx)
    else:
        # Single geometry mode — just body channels, no tabs
        render_channel_list(body_list, f"m{mode_idx}_body", mode_idx)

    st.markdown('</div>', unsafe_allow_html=True)
# ── Add Mode ──────────────────────────────────────────────────────────────────
st.button("＋ Add Mode", on_click=add_mode)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
#  GENERATE
# ══════════════════════════════════════════════════════════════════════════════

if st.button("⚡ Generate .gdtf File", type="primary", key="gen_manual"):
    fname = st.session_state.get("fixture_name", "").strip() or "Unknown Fixture"
    mfr   = st.session_state.get("manufacturer", "").strip() or "Generic"
    cells = int(st.session_state.get("cell_count", 1))
    modes_dict = {
        m["name"]: channel_defs_from_mode(m)
        for m in st.session_state.modes
        if m["name"].strip()
    }
    try:
        xml_data   = build_gdtf(fname, mfr, modes_dict, cell_count=cells)
        gdtf_bytes = create_gdtf_package(xml_data)
        # Count real DMX channels (body + cell × cells, excluding virtual)
        total_dmx = sum(
            len([c for c in b if not c.is_fine_byte]) +
            len([c for c in c_ if not c.is_fine_byte and
                 "virtual" not in c.name.lower()]) * cells
            for b, c_ in modes_dict.values()
        )
        total_sets = sum(
            len(ch.get("slots", []))
            for m in st.session_state.modes
            for ch in (m.get("body_channels", []) + m.get("cell_channels", []))
        )
        cell_info = f" · {cells} cells" if cells > 1 else ""
        st.success(
            f"✅  {total_dmx} DMX channels · {total_sets} channel sets · "
            f"{len(modes_dict)} mode(s){cell_info} · {len(gdtf_bytes):,} bytes"
        )

        # ── Wheel reference validation ─────────────────────────────────────
        wheel_errors = validate_wheel_references(xml_data)
        if wheel_errors:
            st.markdown(
                '<div class="warn-box"><b>⚠ Wheel reference issues detected</b> — ' +
                'MA3 may silently drop affected channels on import:<br><ul>' +
                "".join(f"<li>{e}</li>" for e in wheel_errors) +
                '</ul></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="info-box" style="border-color:#00E000;background:#001A00">' +
                '✔ Wheel references validated — all OK</div>',
                unsafe_allow_html=True
            )

        col_dl, col_xp = st.columns([1, 2])
        with col_dl:
            st.download_button(
                "📦 Download .gdtf", gdtf_bytes,
                file_name=f"{fname.replace(' ','_')}.gdtf",
                mime="application/octet-stream"
            )
            st.markdown("""
            <div class="info-box" style="margin-top:0.8rem;font-size:0.78rem">
            <b>MA3 onPC — place file at:</b><br>
            <code style="font-size:0.7rem">Documents\\MA Lighting Technologies\\grandMA3\\gma3_library\\fixturetypes\\</code><br><br>
            Then: <b>Menu → Patch → Fixture Types → Import → User tab</b>
            </div>
            """, unsafe_allow_html=True)
        with col_xp:
            with st.expander("View description.xml"):
                st.code(xml_data, language="xml")
    except Exception as e:
        st.exception(e)


# ── Attribute reference ───────────────────────────────────────────────────────
st.divider()
with st.expander("📖 Supported Channel Names"):
    cols = st.columns(3)
    items = list(ATTR_MAP.items())
    chunk = len(items) // 3 + 1
    for i, col in enumerate(cols):
        with col:
            for raw, (attr, *_) in items[i*chunk:(i+1)*chunk]:
                st.markdown(
                    f'<span class="badge b-ok">{raw}</span>'
                    f'<span style="color:#999;font-size:0.7rem"> → {attr}</span>',
                    unsafe_allow_html=True
                )
