from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Inner <svg> markup only (paths/shapes) — each entry gets wrapped by `icon()` below.
# Style: 24x24 viewBox, stroke-based, matches the hand-drawn convention already used in
# core_app/partials/navbar.html and listings_app/room_detail.html.
ICONS = {
    # Smoking / substances
    'cigarette-ban': '<path d="M2 15h14v4H2z"/><path d="M16 15h4v4h-4z"/><path d="M18 12v3"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'cigarette':      '<path d="M2 15h14v4H2z"/><path d="M16 15h4v4h-4z"/><path d="M18 12v3"/>',
    'ban':            '<circle cx="12" cy="12" r="9"/><line x1="6" y1="6" x2="18" y2="18"/>',

    # Religion / culture
    'mosque':  '<path d="M12 3l3 4H9l3-4z"/><path d="M5 21V11a7 7 0 0114 0v10"/><path d="M5 21h14"/><path d="M12 21v-6"/>',
    'cross':   '<line x1="12" y1="3" x2="12" y2="21"/><line x1="6" y1="9" x2="18" y2="9"/>',
    'globe':   '<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 010 18 14 14 0 010-18z"/>',
    'utensils':'<path d="M6 3v7a2 2 0 002 2 2 2 0 002-2V3"/><path d="M8 12v9"/><path d="M17 3c-1.5 0-3 1.5-3 4v3h3v9"/>',
    'prayer':  '<path d="M12 3a3 3 0 013 3v2a3 3 0 01-6 0V6a3 3 0 013-3z"/><path d="M6 21v-5a6 6 0 0112 0v5"/>',

    # People / gender / groups
    'person':      '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    'people':      '<circle cx="9" cy="8" r="3.5"/><circle cx="17" cy="9" r="3"/><path d="M2 21c0-3.8 3.1-6.5 7-6.5s7 2.7 7 6.5"/><path d="M15 15c3 .3 5 2.6 5 6"/>',
    'briefcase':   '<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2"/>',
    'plane':       '<path d="M3 13l8-2 6-8 2 2-6 6 8 2v2l-8 1-2 6-2-2 2-6-6-1v-2z"/>',
    'person-ban':  '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/><line x1="3" y1="3" x2="21" y2="21"/>',

    # Pets
    'paw':  '<circle cx="7" cy="8" r="1.6"/><circle cx="12" cy="6" r="1.6"/><circle cx="17" cy="8" r="1.6"/><path d="M12 12c-3 0-5.5 2.3-5.5 5a3 3 0 003 3c1 0 1.8-.5 2.5-1 .7.5 1.5 1 2.5 1a3 3 0 003-3c0-2.7-2.5-5-5.5-5z"/>',
    'dog':  '<path d="M4 10l3-4 3 2 4-2 3 4v6a4 4 0 01-4 4H8a4 4 0 01-4-4v-6z"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/>',
    'cat':  '<path d="M5 4l3 4h8l3-4v9a7 7 0 01-14 0V4z"/><circle cx="9.5" cy="12" r="1"/><circle cx="14.5" cy="12" r="1"/>',

    # Kitchen / food
    'chef-hat':      '<path d="M8 21h8"/><path d="M9 21v-5"/><path d="M15 21v-5"/><path d="M6 10a4 4 0 014-4 3 3 0 015.9-1 4 4 0 013.1 4c0 2.2-1.8 4-4 4H10a4 4 0 01-4-4z"/>',
    'leaf':          '<path d="M5 19c8-1 13-6 14-14-8 1-13 6-14 14z"/><path d="M5 19c2-3 5-6 9-9"/>',
    'fish-ban':      '<path d="M3 12s3-4 8-4 9 4 9 4-4 4-9 4-8-4-8-4z"/><circle cx="17" cy="11" r=".5"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'cart':          '<circle cx="9" cy="20" r="1.5"/><circle cx="17" cy="20" r="1.5"/><path d="M2 3h2l2.6 12.4a2 2 0 002 1.6h8.8a2 2 0 002-1.6L21 7H6"/>',
    'plate':         '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
    'takeout-ban':   '<path d="M6 8h12l-1 12H7L6 8z"/><path d="M9 8V6a3 3 0 016 0v2"/><line x1="3" y1="3" x2="21" y2="21"/>',

    # Noise / schedule
    'moon':          '<path d="M20 14.5A8.5 8.5 0 119.5 4a7 7 0 0010.5 10.5z"/>',
    'music-ban':     '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'party-ban':     '<path d="M4 21l6-14 10 10z"/><path d="M11 8l1-4"/><path d="M15 6l2-3"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'lotus':         '<path d="M12 21c-4-2-6-5-6-9a6 6 0 0112 0c0 4-2 7-6 9z"/><path d="M12 21c-2-3-2-9 0-13"/>',
    'phone-mute':    '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/><line x1="3" y1="3" x2="21" y2="21"/>',

    # Cleanliness
    'broom':         '<path d="M20 4L10 14"/><path d="M6 22l3-3"/><path d="M4 14l6 6-2 2-7-3z"/>',
    'shoe-ban':      '<path d="M3 18v-4l5-2 4 2 6-2 3 3v3z"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'handshake':     '<path d="M2 12l5-4 4 3 3-3 8 5-3 4-5-3-3 3-4-3z"/>',
    'droplet':       '<path d="M12 3s7 7.5 7 12a7 7 0 01-14 0c0-4.5 7-12 7-12z"/>',
    'recycle':       '<path d="M7 19H4a2 2 0 01-1.7-3l3-5"/><path d="M11 5.5l3-2 2 3.5"/><path d="M17 19h3a2 2 0 001.7-3l-3-5"/><path d="M9 19h6"/>',

    # Guests
    'clock':         '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/>',
    'speaker-mute':  '<polygon points="4 9 8 9 13 5 13 19 8 15 4 15 4 9"/><line x1="16" y1="9" x2="21" y2="14"/><line x1="21" y1="9" x2="16" y2="14"/>',

    # Amenities
    'chair':         '<path d="M6 4h12v9H6z"/><path d="M6 13v7"/><path d="M18 13v7"/><path d="M4 20h16"/>',
    'bathtub':       '<path d="M4 12h16v3a5 5 0 01-5 5H9a5 5 0 01-5-5v-3z"/><path d="M4 12V8a2 2 0 012-2"/><path d="M8 20v1"/><path d="M16 20v1"/>',
    'snowflake':     '<line x1="12" y1="2" x2="12" y2="22"/><line x1="4" y1="7" x2="20" y2="17"/><line x1="20" y1="7" x2="4" y2="17"/>',
    'thermometer':   '<path d="M14 14.76V5a2 2 0 00-4 0v9.76a4 4 0 104 0z"/>',
    'shower':        '<path d="M4 12h16"/><path d="M8 4a4 4 0 014 4v4"/><line x1="8" y1="16" x2="8" y2="16.01"/><line x1="12" y1="16" x2="12" y2="16.01"/><line x1="16" y1="16" x2="16" y2="16.01"/><line x1="8" y1="20" x2="8" y2="20.01"/><line x1="12" y1="20" x2="12" y2="20.01"/><line x1="16" y1="20" x2="16" y2="20.01"/>',
    'window':        '<rect x="4" y="4" width="16" height="16" rx="1"/><line x1="12" y1="4" x2="12" y2="20"/><line x1="4" y1="12" x2="20" y2="12"/>',
    'garden':        '<path d="M12 21V9"/><path d="M12 9C7 9 5 5 5 5s0 6 7 6z"/><path d="M12 9c5 0 7-4 7-4s0 6-7 6z"/>',
    'box':           '<path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
    'tv':             '<rect x="3" y="5" width="18" height="12" rx="1"/><line x1="8" y1="21" x2="16" y2="21"/>',
    'elevator':       '<rect x="5" y="3" width="14" height="18" rx="1"/><polyline points="10 9 12 7 14 9"/><polyline points="10 15 12 17 14 15"/>',
    'sofa':            '<path d="M4 12v5a1 1 0 001 1h1a1 1 0 001-1v-1h10v1a1 1 0 001 1h1a1 1 0 001-1v-5"/><path d="M4 12a2 2 0 012-2h12a2 2 0 012 2"/><path d="M6 10V7a2 2 0 012-2h8a2 2 0 012 2v3"/>',
    'monitor':         '<rect x="3" y="4" width="18" height="12" rx="1"/><line x1="8" y1="20" x2="16" y2="20"/><line x1="12" y1="16" x2="12" y2="20"/>',
    'lock':            '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',

    # Bills
    'bolt':          '<polygon points="13 2 4 14 11 14 10 22 20 10 13 10 13 2"/>',
    'wifi':          '<path d="M2 8.5a16 16 0 0120 0"/><path d="M5.5 12a11 11 0 0113 0"/><path d="M9 15.5a6 6 0 016 0"/><circle cx="12" cy="19" r="1"/>',
    'receipt':       '<path d="M6 2h12v20l-3-2-3 2-3-2-3 2V2z"/><line x1="9" y1="7" x2="15" y2="7"/><line x1="9" y1="11" x2="15" y2="11"/>',
    'flame':         '<path d="M12 2c2 4-2 5-2 9a4 4 0 008 0c0-2-1-3-1-3s2 1 2 5a7 7 0 11-14 0c0-5 4-6 7-11z"/>',

    # Work / study
    'plug':          '<path d="M9 2v6"/><path d="M15 2v6"/><path d="M6 8h12v4a6 6 0 01-12 0V8z"/><path d="M12 18v4"/>',
    'printer':       '<polyline points="6 9 6 2 18 2 18 9"/><rect x="6" y="14" width="12" height="8"/><rect x="4" y="9" width="16" height="7" rx="1"/>',

    # Building facilities
    'waves':         '<path d="M2 9c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/><path d="M2 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0"/>',
    'dumbbell':      '<path d="M4 8v8"/><path d="M20 8v8"/><path d="M2 10v4h4v-4z"/><path d="M18 10v4h4v-4z"/><line x1="6" y1="12" x2="18" y2="12"/>',
    'sunset':        '<path d="M12 3v6"/><path d="M5.6 10.6l1.4 1.4"/><path d="M18.4 10.6l-1.4 1.4"/><line x1="2" y1="16" x2="22" y2="16"/><path d="M6 16a6 6 0 0112 0"/><line x1="4" y1="20" x2="20" y2="20"/>',
    'coffee':        '<path d="M4 8h13a3 3 0 010 6h-1"/><path d="M4 8v6a4 4 0 004 4h4a4 4 0 004-4V8"/><line x1="7" y1="3" x2="7" y2="5"/><line x1="11" y1="3" x2="11" y2="5"/>',
    'steam':         '<path d="M6 21h12"/><path d="M6 21a6 6 0 016-11 6 6 0 016 11"/><path d="M9 6c0-2 1-2 1-4"/><path d="M14 6c0-2 1-2 1-4"/>',

    # Security
    'shield':        '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    'camera':        '<rect x="2" y="7" width="20" height="14" rx="2"/><circle cx="12" cy="14" r="4"/><path d="M8 7l2-3h4l2 3"/>',
    'gate':          '<rect x="4" y="4" width="16" height="16" rx="1"/><line x1="4" y1="10" x2="20" y2="10"/><line x1="12" y1="4" x2="12" y2="20"/>',
    'key':           '<circle cx="8" cy="8" r="4"/><path d="M11 11l9 9"/><path d="M16 16l3-3"/><path d="M18 18l2-2"/>',
    'smartphone-lock':'<rect x="7" y="2" width="10" height="20" rx="2"/><rect x="9.5" y="10" width="5" height="4" rx="1"/><path d="M10.5 10V8.5a1.5 1.5 0 013 0V10"/>',
    'bell':          '<path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 01-3.4 0"/>',

    # Parking / transport
    'car':           '<path d="M5 17h14M5 17a2 2 0 01-2-2v-2l2-5h14l2 5v2a2 2 0 01-2 2M5 17v2a1 1 0 001 1h1a1 1 0 001-1v-2M17 17v2a1 1 0 001 1h1a1 1 0 001-1v-2"/>',
    'parking':       '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 16V7h4a3 3 0 010 6H9"/>',
    'train':         '<rect x="5" y="3" width="14" height="14" rx="4"/><line x1="5" y1="12" x2="19" y2="12"/><circle cx="9" cy="15.5" r="0" /><circle cx="8.5" cy="15" r=".8"/><circle cx="15.5" cy="15" r=".8"/><path d="M8 21l1.5-3h5L16 21"/>',
    'bus':           '<rect x="3" y="5" width="18" height="12" rx="2"/><line x1="3" y1="11" x2="21" y2="11"/><circle cx="7.5" cy="19" r="1.5"/><circle cx="16.5" cy="19" r="1.5"/>',
    'bike':          '<circle cx="6" cy="17" r="3"/><circle cx="18" cy="17" r="3"/><path d="M6 17l4-9h4l3 6"/><path d="M10 8h3"/>',

    # Laundry
    'washer':        '<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="13" r="5"/><circle cx="7" cy="6" r=".6"/>',
    'shirt':         '<path d="M8 3l4 2 4-2 3 4-3 2v10H8V9L5 7z"/>',
    'clothesline':   '<line x1="2" y1="6" x2="22" y2="6"/><path d="M7 6v5l-2 3"/><path d="M14 6v3l2 4"/>',

    # Financial
    'bank':          '<line x1="3" y1="21" x2="21" y2="21"/><line x1="5" y1="21" x2="5" y2="10"/><line x1="19" y1="21" x2="19" y2="10"/><polygon points="12 3 21 9 3 9"/>',
    'dollar':        '<line x1="12" y1="2" x2="12" y2="22"/><path d="M17 6H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>',
    'calendar':      '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    'credit-card':   '<rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>',

    # Safety
    'first-aid':     '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M8 6V5a2 2 0 012-2h4a2 2 0 012 2v1"/><line x1="12" y1="10" x2="12" y2="16"/><line x1="9" y1="13" x2="15" y2="13"/>',
    'cloud':         '<path d="M17 18a4 4 0 000-8 5.5 5.5 0 00-10.6 1.5A4 4 0 007 18h10z"/>',

    # Language
    'message':       '<path d="M21 11.5a8.5 8.5 0 01-8.5 8.5 8.4 8.4 0 01-4-1L3 20l1-4.5A8.5 8.5 0 1121 11.5z"/>',
    'map-pin-region':'<path d="M12 21s7-6.5 7-12a7 7 0 00-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',

    # UI chrome
    'lightbulb':     '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a6 6 0 00-4 10.5c.6.6 1 1.4 1 2.5h6c0-1.1.4-1.9 1-2.5A6 6 0 0012 2z"/>',
    'map-pin':       '<path d="M12 21s7-6.5 7-12a7 7 0 00-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    'folder':        '<path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>',
    'sparkle':       '<path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8z"/><path d="M19 15l.7 2.1L22 18l-2.3.9L19 21l-.7-2.1L16 18l2.3-.9z"/>',
    'spinner':       '<g style="animation:spin 1s linear infinite;transform-origin:12px 12px"><path d="M12 3a9 9 0 019 9"/></g>',
    'close':         '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    'rocket':        '<path d="M12 2c3 1 5 4 5 8 0 3-1 5-2 6l-3 3-3-3c-1-1-2-3-2-6 0-4 2-7 5-8z"/><circle cx="12" cy="9" r="1.5"/><path d="M8 16l-2 5 5-2"/><path d="M16 16l2 5-5-2"/>',
    'check':         '<polyline points="20 6 9 17 4 12"/>',
    'chevron-left':  '<polyline points="15 18 9 12 15 6"/>',
    'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
    'warning':       '<path d="M12 3l10 18H2z"/><line x1="12" y1="9" x2="12" y2="14"/><line x1="12" y1="17" x2="12" y2="17.01"/>',
    'tag':           '<path d="M20.6 12.9L12 21.5 2.5 12 2.5 2.5 12 2.5 20.6 11z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    'edit':          '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/>',
    'save':          '<path d="M17 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V7l-4-4z"/><path d="M17 3v4H8V3M12 12v5m0 0l-2-2m2 2l2-2"/>',
    'notepad':       '<path d="M8 2v3"/><path d="M16 2v3"/><rect x="4" y="4" width="16" height="18" rx="2"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="13" y2="15"/>',
    'clipboard':     '<rect x="6" y="4" width="12" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><line x1="9" y1="11" x2="15" y2="11"/><line x1="9" y1="15" x2="15" y2="15"/>',
    'bed':           '<path d="M2 20v-7a2 2 0 012-2h16a2 2 0 012 2v7"/><path d="M2 17h20"/><path d="M6 11V6a2 2 0 012-2h3v7"/><path d="M13 11V6a2 2 0 012-2h3a2 2 0 012 2v5"/>',
    'home':          '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    'bunk-bed':      '<path d="M2 21v-6a2 2 0 012-2h16a2 2 0 012 2v6"/><path d="M2 15V9a2 2 0 012-2h16a2 2 0 012 2v6"/><path d="M2 21h20"/><path d="M6 13V7"/>',
    'house-check':   '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',

    # Map POI markers
    'graduation-cap':'<path d="M2 9l10-5 10 5-10 5-10-5z"/><path d="M6 11v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>',
    'hospital':      '<rect x="3" y="4" width="18" height="17" rx="1"/><line x1="12" y1="9" x2="12" y2="15"/><line x1="9" y1="12" x2="15" y2="12"/>',
    'school':        '<path d="M3 10l9-6 9 6-9 6-9-6z"/><path d="M7 12.5V18l5 3 5-3v-5.5"/>',
    'pharmacy':      '<circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>',

    # UI chrome (round 2 — room_detail / listings pages)
    'sliders':       '<line x1="4" y1="6" x2="20" y2="6"/><circle cx="9" cy="6" r="2"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="9" cy="18" r="2"/>',
    'star':          '<polygon points="12 2 15 9 22 9.5 17 14.5 18.5 22 12 18 5.5 22 7 14.5 2 9.5 9 9"/>',
    'star-outline':  '<polygon points="12 2 15 9 22 9.5 17 14.5 18.5 22 12 18 5.5 22 7 14.5 2 9.5 9 9"/>',
    'camera-photo':  '<rect x="2" y="7" width="20" height="14" rx="2"/><circle cx="12" cy="14" r="4"/><path d="M8 7l2-3h4l2 3"/>',
    'hand-point':    '<path d="M8 13V5a1.5 1.5 0 013 0v6"/><path d="M11 6a1.5 1.5 0 013 0v5"/><path d="M14 7a1.5 1.5 0 013 0v4"/><path d="M17 9a1.5 1.5 0 013 0v5a6 6 0 01-6 6h-2a6 6 0 01-5-2.7L4 13a1.5 1.5 0 012.5-1.6L8 13"/>',
    'wine-ban':      '<path d="M8 3h8l-1 8a3 3 0 01-6 0L8 3z"/><path d="M12 14v7"/><path d="M9 21h6"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'user-x':        '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4.4 3.6-7 7-7s7 2.6 7 7"/><line x1="16" y1="9" x2="21" y2="14"/><line x1="21" y1="9" x2="16" y2="14"/>',
    'man':           '<circle cx="12" cy="7" r="4"/><path d="M5 21c0-4.4 3.1-7 7-7s7 2.6 7 7"/>',
    'woman':         '<circle cx="12" cy="7" r="4"/><path d="M5 21c0-4.4 3.1-7 7-7s7 2.6 7 7"/><path d="M12 14v7"/>',
    'megaphone-ban': '<path d="M3 11v2a2 2 0 002 2h1l3 5 1-5h1l7 4V6l-7 4H9L6 9H5a2 2 0 00-2 2z"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'phone-ban':     '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'sunrise':       '<path d="M12 2v6"/><path d="M5.6 8.6l1.4 1.4"/><path d="M18.4 8.6l-1.4 1.4"/><line x1="2" y1="14" x2="22" y2="14"/><path d="M6 14a6 6 0 0112 0"/><line x1="4" y1="18" x2="20" y2="18"/><line x1="2" y1="22" x2="22" y2="22"/>',
    'shield-ban':    '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><line x1="7" y1="7" x2="17" y2="17"/>',
    'lock-open':     '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 017.5-2"/>',
    'door-ban':      '<rect x="6" y="3" width="12" height="18" rx="1"/><line x1="14" y1="12" x2="14" y2="12.01"/><line x1="3" y1="3" x2="21" y2="21"/>',
    'bell-ring':     '<path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 01-3.4 0"/><path d="M4 4l-2 2"/><path d="M20 4l2 2"/>',
    'clock-ban':     '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/><line x1="4" y1="4" x2="20" y2="20"/>',
    'flag':          '<path d="M4 21V4"/><path d="M4 4h13l-2 4 2 4H4"/>',
    'salad':         '<path d="M4 12a8 8 0 0116 0z"/><path d="M2 12h20"/><path d="M12 12V6"/><path d="M8 6l1-3"/><path d="M16 6l-1-3"/>',
    'fish':          '<path d="M3 12s3-4 8-4 9 4 9 4-4 4-9 4-8-4-8-4z"/><circle cx="17" cy="11" r=".5"/>',
    'award':         '<circle cx="12" cy="8" r="6"/><path d="M9 13.5L7 22l5-3 5 3-2-8.5"/>',
    'photo':         '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>',
    'bookmark':      '<path d="M6 3h12v18l-6-4-6 4V3z"/>',
    'link':          '<path d="M10 14a5 5 0 007.5.5l2-2a5 5 0 00-7-7l-1.5 1.5"/><path d="M14 10a5 5 0 00-7.5-.5l-2 2a5 5 0 007 7l1.5-1.5"/>',
    'pin':           '<path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"/>',
    'mailbox':       '<rect x="3" y="9" width="14" height="10" rx="2"/><path d="M3 9a4 4 0 014-4h6a4 4 0 014 4"/><line x1="19" y1="13" x2="22" y2="13"/>',
    'plus':          '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    'heart':         '<path d="M12 21s-7.5-4.6-10-9.3C.5 8.4 2.2 5 5.6 5c2 0 3.4 1 4.4 2.5C11 6 12.4 5 14.4 5c3.4 0 5.1 3.4 3.6 6.7C19.5 16.4 12 21 12 21z"/>',
}


def _wrap(inner, size, color, filled=False):
    color_attr = f' style="color:{color}"' if color else ''
    fill = 'currentColor' if filled else 'none'
    return mark_safe(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="{fill}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true"{color_attr}>{inner}</svg>'
    )


@register.simple_tag
def icon(name, size=18, color=None, filled=False):
    """Usage: {% icon 'smoking' size=18 %} or {% icon 'smoking' size=18 color='#fff' %} or {% icon 'heart' filled=True %}"""
    inner = ICONS.get(name)
    if inner is None:
        return ''
    return _wrap(inner, size, color, filled)
