#!/usr/bin/env python3
"""
Kenka Bancho 6: Soul & Blood - English patch installer (beta)

Builds the English mod files from YOUR OWN legally dumped copy of the Japanese game.  This tool and kb6_patch.dat contain no game files:
the patch data only holds the differences (new English text, redrawn images, a rebuilt font) that are applied to the files read from
your dump.  Nothing is ever written to your dump.

Usage
    python kb6_patcher.py "Kenko Bancho 6.3ds"              dump file: .3ds / .cci / .cxi / .cia (must be DECRYPTED)
    python kb6_patcher.py "C:\\path\\to\\extracted\\romfs"    or a folder holding the extracted RomFS (e.g. from Azahar: right-click > Dump RomFS)
Options
    --out DIR        where to write the result (default: ./KB6_English_Output)
    --target T       azahar | luma | both   (default: both)
    --no-exheader    leave out the optional New 3DS speed file for Luma3DS
    --force          continue even if a file does not match the expected Japanese version (not recommended)
    --list           only show what the dump contains, write nothing
Requires Python 3.8 or newer (standard library only).
"""
import argparse
import hashlib
import json
import lzma
import os
import struct
import sys
import time

TITLE_ID = '00040000000F4F00'
PATCH_FILE = 'kb6_patch.dat'


# ----------------------------------------------------------------------------------------------------------------- delta
def apply_delta(src, delta, out_len):
    out = bytearray()
    p = 0
    prev_end = 0
    dl = len(delta)
    while p < dl:
        v = shift = 0
        while True:
            b = delta[p]
            p += 1
            v |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                break
        ln, is_add = v >> 1, v & 1
        if is_add:
            out += delta[p:p + ln]
            p += ln
        else:
            v = shift = 0
            while True:
                b = delta[p]
                p += 1
                v |= (b & 0x7F) << shift
                shift += 7
                if not b & 0x80:
                    break
            off = prev_end + ((v >> 1) if not v & 1 else -((v + 1) >> 1))
            out += src[off:off + ln]
            prev_end = off + ln
    if len(out) != out_len:
        raise ValueError('patch data is damaged (length mismatch)')
    return bytes(out)


def sha1(b):
    return hashlib.sha1(b).hexdigest()


# ------------------------------------------------------------------------------------------------------ 3DS file readers
class DumpError(Exception):
    pass


def _u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def _u64(b, o):
    return struct.unpack_from('<Q', b, o)[0]


def _align(n, a):
    return (n + a - 1) // a * a


def _lz_decompress_backwards(data):
    """Nintendo 'backwards LZ' used for the compressed .code section of ExeFS."""
    if len(data) < 8:
        raise DumpError('code section too short')
    top_bottom, extra = struct.unpack_from('<II', data, len(data) - 8)
    if extra == 0:
        return bytes(data)
    hdr_len = top_bottom >> 24
    enc_len = top_bottom & 0xFFFFFF
    out = bytearray(data) + bytearray(extra)
    src = len(data) - hdr_len
    dst = len(data) + extra
    stop = len(data) - enc_len
    while src > stop and dst > 0:
        src -= 1
        flags = out[src]
        for _ in range(8):
            if src <= stop or dst <= 0:
                break
            if flags & 0x80:
                src -= 2
                pair = out[src] | (out[src + 1] << 8)
                ln = (pair >> 12) + 3
                disp = (pair & 0xFFF) + 3
                for _k in range(ln):
                    dst -= 1
                    out[dst] = out[dst + disp]
            else:
                src -= 1
                dst -= 1
                out[dst] = out[src]
            flags = (flags << 1) & 0xFF
    return bytes(out)


class RomSource:
    """Reads files out of a decrypted .3ds/.cci/.cxi/.cia without extracting it."""

    def __init__(self, path):
        self.f = open(path, 'rb')
        self.path = path
        self.exheader = None
        self.code = None
        self._open_ncch()
        self._open_romfs()

    def _read(self, off, n):
        self.f.seek(off)
        b = self.f.read(n)
        if len(b) != n:
            raise DumpError('unexpected end of file (damaged or truncated dump?)')
        return b

    def _open_ncch(self):
        head = self._read(0, 0x200)
        base = 0
        if head[0x100:0x104] == b'NCSD':
            base = _u32(head, 0x120) * 0x200
        elif head[0x100:0x104] == b'NCCH':
            base = 0
        elif _u32(head, 0) == 0x2020:               # CIA header size
            cert, tik, tmd, meta = _u32(head, 8), _u32(head, 0xC), _u32(head, 0x10), _u32(head, 0x14)
            off = _align(0x2020, 64)
            off = _align(off + cert, 64)
            off = _align(off + tik, 64)
            off = _align(off + tmd, 64)
            off = _align(off + meta, 64)
            base = off
        else:
            raise DumpError('not a .3ds/.cci/.cxi/.cia file')
        h = self._read(base, 0x200)
        if h[0x100:0x104] != b'NCCH':
            raise DumpError('the game data looks ENCRYPTED. This patcher needs a decrypted dump (or a folder of extracted RomFS files).')
        flags = h[0x188:0x190]
        if not flags[7] & 4:
            raise DumpError('the game data is marked as encrypted. Use a decrypted dump (or dump the RomFS from Azahar and pass that folder).')
        self.base = base
        self.hdr = h
        self.unit = 0x200 << flags[6] if flags[6] < 8 else 0x200
        self.program_id = '%016X' % _u64(h, 0x118)
        self.product_code = h[0x150:0x160].split(b'\0')[0].decode('ascii', 'replace')
        exh_size = _u32(h, 0x180)
        if exh_size:
            self.exheader = self._read(base + 0x200, 0x800)

    def _open_romfs(self):
        h = self.hdr
        roff, rsize = _u32(h, 0x1B0) * self.unit, _u32(h, 0x1B4) * self.unit
        if not roff:
            raise DumpError('this dump has no RomFS')
        r0 = self.base + roff
        ivfc = self._read(r0, 0x60)
        if ivfc[:4] != b'IVFC':
            raise DumpError('RomFS header not found (encrypted dump?)')
        master = _u32(ivfc, 8)
        l3_log2 = _u32(ivfc, 0x4C)
        region = _align(0x60 + master, 1 << l3_log2)
        self.l3 = r0 + region        # on disk the actual file system (level 3) comes first, the hash levels follow it
        lh = self._read(self.l3, 0x28)
        if _u32(lh, 0) != 0x28:
            raise DumpError('RomFS level 3 header not found')
        self.dir_off, self.dir_size = _u32(lh, 0x0C), _u32(lh, 0x10)
        self.file_off, self.file_size = _u32(lh, 0x1C), _u32(lh, 0x20)
        self.data_off = _u32(lh, 0x24)
        self.dirs = self._read(self.l3 + self.dir_off, self.dir_size)
        self.files_meta = self._read(self.l3 + self.file_off, self.file_size)
        self.index = {}
        self._walk(0, '')

    def _name(self, blob, o, nlen):
        return blob[o:o + nlen].decode('utf-16-le')

    def _walk(self, d, prefix):
        child_dir, child_file = _u32(self.dirs, d + 8), _u32(self.dirs, d + 12)
        fe = child_file
        while fe != 0xFFFFFFFF:
            nlen = _u32(self.files_meta, fe + 0x1C)
            name = self._name(self.files_meta, fe + 0x20, nlen)
            self.index[prefix + name] = (_u64(self.files_meta, fe + 8), _u64(self.files_meta, fe + 0x10))
            fe = _u32(self.files_meta, fe + 4)
        de = child_dir
        while de != 0xFFFFFFFF:
            nlen = _u32(self.dirs, de + 0x14)
            name = self._name(self.dirs, de + 0x18, nlen)
            self._walk(de, prefix + name + '/')
            de = _u32(self.dirs, de + 4)

    def names(self):
        return self.index.keys()

    def get(self, rel):
        o, n = self.index[rel]
        return self._read(self.l3 + self.data_off + o, n)

    def exefs_code(self):
        h = self.hdr
        eoff, esize = _u32(h, 0x1A0) * self.unit, _u32(h, 0x1A4) * self.unit
        if not eoff:
            return None
        hdr = self._read(self.base + eoff, 0x200)
        for i in range(10):
            nm = hdr[i * 16:i * 16 + 8].rstrip(b'\0')
            if nm == b'.code':
                off, size = _u32(hdr, i * 16 + 8), _u32(hdr, i * 16 + 12)
                raw = self._read(self.base + eoff + 0x200 + off, size)
                compressed = bool(self.exheader[0xD] & 1) if self.exheader else False
                return _lz_decompress_backwards(raw) if compressed else raw
        return None


class FolderSource:
    """An already extracted RomFS folder."""

    def __init__(self, path):
        root = path
        if os.path.isdir(os.path.join(path, 'romfs')):
            root = os.path.join(path, 'romfs')
        self.root = root
        self.exheader = None
        self.program_id = None
        self.product_code = None
        self.index = {}
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, root).replace('\\', '/')
                self.index[rel] = (full, os.path.getsize(full))

    def names(self):
        return self.index.keys()

    def get(self, rel):
        with open(self.index[rel][0], 'rb') as fh:
            return fh.read()

    def exefs_code(self):
        return None


def open_source(path):
    if os.path.isdir(path):
        return FolderSource(path)
    return RomSource(path)


# ----------------------------------------------------------------------------------------------------------- patch data
class PatchData:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.blob = f.read()
        if self.blob[:4] != b'KB6P':
            raise DumpError('%s is not a valid patch file' % path)
        mlen = _u32(self.blob, 8)
        self.manifest = json.loads(self.blob[12:12 + mlen].decode('utf-8'))
        self.base = 12 + mlen

    def entry_bytes(self, e):
        return lzma.decompress(self.blob[self.base + e['off']:self.base + e['off'] + e['len']])


def say(msg=''):
    print(msg)
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description='Kenka Bancho 6 English patch installer')
    ap.add_argument('dump', help='your decrypted game dump (.3ds/.cci/.cxi/.cia) or a folder with the extracted RomFS')
    ap.add_argument('--out', default='KB6_English_Output')
    ap.add_argument('--target', choices=['azahar', 'luma', 'both'], default='both')
    ap.add_argument('--no-exheader', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    pd = PatchData(os.path.join(here, PATCH_FILE))
    man = pd.manifest
    say('Kenka Bancho 6 English patch %s' % man['version'])
    try:
        src = open_source(a.dump)
    except DumpError as e:
        say('\nERROR: %s' % e)
        return 2
    except FileNotFoundError:
        say('\nERROR: cannot find %s' % a.dump)
        return 2
    if src.program_id:
        say('Game found: %s (title ID %s)' % (src.product_code or '?', src.program_id))
        if src.program_id != TITLE_ID:
            say('ERROR: this is not Kenka Bancho 6: Soul & Blood (expected title ID %s).' % TITLE_ID)
            return 2
    say('Files in the dump: %d' % len(list(src.names())))
    if a.list:
        for n in sorted(src.names())[:50]:
            say('  ' + n)
        return 0

    # ---- executable check (only possible with a ROM file)
    code_ok = None
    code = src.exefs_code()
    if code is not None:
        code_ok = sha1(code) == man['code_sha1']
        say('Game executable: %s' % ('matches the Japanese version this patch was made for' if code_ok else 'DOES NOT MATCH (different version or region?)'))
        if not code_ok and not a.force:
            say('\nStopping: the code patch would damage this version. Use --force only if you know what you are doing.')
            return 3
    else:
        say('Note: the executable cannot be checked from a folder. Make sure the dump is the original Japanese version.')

    out_root = os.path.abspath(a.out)
    want_az = a.target in ('azahar', 'both')
    want_lu = a.target in ('luma', 'both')
    az_romfs = os.path.join(out_root, 'azahar_or_citra', 'load', 'mods', TITLE_ID, 'romfs')
    lu_romfs = os.path.join(out_root, 'luma3ds', 'luma', 'titles', TITLE_ID, 'romfs')

    entries = [e for e in man['entries'] if e['kind'] == 'delta']
    say('\nPatching %d files ...' % len(entries))
    t0 = time.time()
    bad = []
    done = 0
    for e in entries:
        rel = e['path']
        if rel not in src.index:
            bad.append((rel, 'missing from your dump'))
            continue
        original = src.get(rel)
        if sha1(original) != e['sha1_src']:
            bad.append((rel, 'differs from the expected Japanese version'))
            if not a.force:
                continue
        new = apply_delta(original, pd.entry_bytes(e), e['size'])
        if sha1(new) != e['sha1_tgt']:
            bad.append((rel, 'result check failed'))
            continue
        for ok, root in ((want_az, az_romfs), (want_lu, lu_romfs)):
            if ok:
                dst = os.path.join(root, *rel.split('/'))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, 'wb') as fh:
                    fh.write(new)
        done += 1
        if done % 40 == 0 or done == len(entries):
            say('  %d / %d  (%.0fs)' % (done, len(entries), time.time() - t0))
    if bad:
        say('\n%d file(s) could not be patched:' % len(bad))
        for rel, why in bad[:12]:
            say('  %s: %s' % (rel, why))
        if len(bad) > 12:
            say('  ...')
        say('\nThe output is INCOMPLETE. Please check that your dump is the original, unmodified Japanese version, then run again.')
        return 4

    # ---- extras: code patch, config, exheader
    blobs = {e['name']: pd.entry_bytes(e) for e in man['entries'] if e['kind'] == 'extra'}
    if want_az:
        d = os.path.join(out_root, 'azahar_or_citra', 'load', 'mods', TITLE_ID, 'exefs')
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'code.ips'), 'wb').write(blobs['code.ips'])
        d = os.path.join(out_root, 'azahar_or_citra', 'config', 'custom')
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, TITLE_ID + '.ini'), 'wb').write(blobs['azahar_game_config.ini'])
    if want_lu:
        d = os.path.join(out_root, 'luma3ds', 'luma', 'titles', TITLE_ID)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'code.ips'), 'wb').write(blobs['code.ips'])
        if not a.no_exheader:
            open(os.path.join(d, 'exheader.bin'), 'wb').write(blobs['exheader.bin'])

    say('\nDone! The English files are in:\n  %s\n' % out_root)
    if want_az:
        say('AZAHAR / CITRA:  copy  azahar_or_citra\\load  into your emulator user folder (File > Open Azahar Folder),')
        say('                 so you get  <user folder>/load/mods/%s/...   then restart the game.' % TITLE_ID)
        say('                 Optional: copy azahar_or_citra\\config\\custom into <user folder>/config/ for the recommended per-game settings.')
    if want_lu:
        say('REAL 3DS (Luma3DS): copy  luma3ds\\luma  onto the root of the SD card (merge folders) and turn on')
        say('                 "Enable game patching" in the Luma3DS config menu (hold SELECT while booting).')
        say('                 The optional exheader.bin only helps New 3DS / New 2DS XL consoles; delete it if the game ever crashes.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
