"""Read and replace icon groups in a Windows DLL (used by make_folder_icons.py).

An icon group (RT_GROUP_ICON) is a small directory that points at one RT_ICON
resource per size. group_to_ico() rebuilds a normal .ico file from it.
write_res() writes icon groups to a .res file that a build tool puts in a DLL.
"""
import io
import struct

import pefile

RT_ICON, RT_GROUP_ICON = 3, 14


def _resources(pe, rtype):
    for t in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if t.id == rtype:
            for e in t.directory.entries:
                if e.id is not None:
                    d = e.directory.entries[0].data.struct
                    yield e.id, pe.get_data(d.OffsetToData, d.Size)


def load(path):
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories([pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
    return dict(_resources(pe, RT_GROUP_ICON)), dict(_resources(pe, RT_ICON))


def group_to_ico(groups, icons, gid):
    data = groups[gid]
    _, _, count = struct.unpack_from("<HHH", data, 0)
    entries, blobs = [], []
    for i in range(count):
        w, h, cc, r, planes, bpp, size, iid = struct.unpack_from("<BBBBHHIH", data, 6 + i * 14)
        if iid in icons:
            entries.append((w, h, cc, r, planes, bpp))
            blobs.append(icons[iid])
    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(entries)))
    offset = 6 + 16 * len(entries)
    for e, b in zip(entries, blobs):
        out.write(struct.pack("<BBBBHHII", *e, len(b), offset))
        offset += len(b)
    for b in blobs:
        out.write(b)
    return out.getvalue()


def write_res(res_path, new_groups, first_icon_id=1000):
    """Writes a .res file (compiled Win32 resources) holding the icon groups.

    new_groups: {group id: .ico bytes}. Each .ico image becomes an RT_ICON
    resource and each group an RT_GROUP_ICON that points at them. Icon ids
    must stay below 32768: the .NET build reads them as signed 16-bit numbers.
    """
    def entry(rtype, rid, data, flags):
        hdr = struct.pack("<IIHHHHIHHII", len(data), 32, 0xFFFF, rtype, 0xFFFF, rid, 0, flags, 0x0409, 0, 0)
        return hdr + data + b"\0" * (-len(data) % 4)

    out = bytearray(struct.pack("<IIHHHHIHHII", 0, 32, 0xFFFF, 0, 0xFFFF, 0, 0, 0, 0, 0, 0))
    next_id = first_icon_id
    for gid, ico in new_groups.items():
        _, _, count = struct.unpack_from("<HHH", ico, 0)
        grp = bytearray(struct.pack("<HHH", 0, 1, count))
        for i in range(count):
            w, h, cc, r, planes, bpp, size, off = struct.unpack_from("<BBBBHHII", ico, 6 + i * 16)
            out += entry(RT_ICON, next_id, ico[off:off + size], 0x1010)
            grp += struct.pack("<BBBBHHIH", w, h, cc, r, planes, bpp, size, next_id)
            next_id += 1
        out += entry(RT_GROUP_ICON, gid, bytes(grp), 0x1030)
    with open(res_path, "wb") as f:
        f.write(out)
