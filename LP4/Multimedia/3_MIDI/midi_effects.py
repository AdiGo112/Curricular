# =========================================================
# ASSIGNMENT 3
# Create a MIDI file, edit it with guitar effects
# (bend, slide, vibrato, hammer-on / pull-off) and
# convert MIDI to WAV
# =========================================================
#
#   sample.mid  : plain guitar riff (A minor pentatonic)
#   edited.mid  : same riff + effects, written as real MIDI
#                 messages:
#      Bend        -> Pitch Bend rising +2 semitones, then release
#      Slide       -> Pitch Bend glide from one fret to another
#      Vibrato     -> fast Pitch Bend wobble (6 Hz, +/- 0.4 semitone)
#      Hammer-on / -> next note starts without a new pick:
#      Pull-off       lower velocity + Legato pedal (CC 68)
#   sample.wav / edited.wav : rendered by reading the .mid files
#                             back and playing them with a small
#                             plucked-string synthesizer
#
# No MIDI library is needed - the file format is written byte
# by byte, so every message can be explained in the viva.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install numpy
#   python midi_effects.py               (create, edit, convert)
#   python midi_effects.py song.mid      (only convert a .mid to .wav)
#
# Open the .mid files in LMMS / MuseScore / TuxGuitar to view
# or play them (see README.md).
#
# =========================================================

import os
import struct
import sys
import wave

import numpy as np

TPQ = 480                  # ticks per quarter note
TEMPO = 500000             # microseconds per quarter note (= 120 BPM)
BEND_RANGE = 12            # pitch-bend range set with RPN 0 (semitones)
GUITAR = 25                # General MIDI program 26 "Acoustic Guitar (steel)" (0-based 25)
RATE = 22050               # WAV sample rate

E, Q, H = TPQ // 2, TPQ, TPQ * 2   # eighth, quarter, half note in ticks
A3, C4, D4, E4, G4, A4 = 57, 60, 62, 64, 67, 69


# =========================================================
# MIDI WRITER
# =========================================================

def vlq(n):
    """Variable-length quantity: 7 bits per byte, high bit = 'more bytes follow'."""
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def bend_bytes(semitones, ch=0):
    """Pitch Bend message: 14-bit value, 8192 = no bend."""
    value = int(round(8192 + semitones * 8192 / BEND_RANGE))
    value = max(0, min(16383, value))
    return bytes([0xE0 | ch, value & 0x7F, value >> 7])


class Track:
    def __init__(self):
        self.events = []          # (absolute tick, order, bytes)

    def add(self, tick, data, order=1):
        self.events.append((tick, order, data))

    def note(self, start, length, pitch, velocity=100, ch=0):
        self.add(start, bytes([0x90 | ch, pitch, velocity]), 2)
        self.add(start + length, bytes([0x80 | ch, pitch, 0]), 0)   # note-offs first at same tick

    def cc(self, tick, number, value, ch=0):
        self.add(tick, bytes([0xB0 | ch, number, value]))

    def bend(self, tick, semitones, ch=0):
        self.add(tick, bend_bytes(semitones, ch))

    def to_bytes(self):
        body, last = b"", 0
        for tick, _, data in sorted(self.events, key=lambda e: (e[0], e[1])):
            body += vlq(tick - last) + data
            last = tick
        body += vlq(0) + b"\xff\x2f\x00"                              # End of Track
        return b"MTrk" + struct.pack(">I", len(body)) + body


def save_midi(path, track):
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TPQ)            # format 0, 1 track
    with open(path, "wb") as f:
        f.write(header + track.to_bytes())


def new_guitar_track(name):
    t = Track()
    t.add(0, b"\xff\x03" + vlq(len(name)) + name.encode(), 0)       # track name
    t.add(0, b"\xff\x51\x03" + TEMPO.to_bytes(3, "big"), 0)          # tempo
    t.add(0, bytes([0xC0, GUITAR]), 0)                               # program change
    # RPN 0,0 = pitch bend sensitivity -> BEND_RANGE semitones
    for number, value in ((101, 0), (100, 0), (6, BEND_RANGE), (38, 0), (101, 127), (100, 127)):
        t.cc(0, number, value)
    return t


# =========================================================
# THE RIFF (plain and with effects)
# =========================================================
#
# Each bar demonstrates one technique. Plain version just
# plays the notes; edited version adds the effect messages.
#

def build(with_effects):
    t = new_guitar_track("Riff with effects" if with_effects else "Plain riff")
    bar = 4 * Q

    # Bar 1: intro notes (no effect)
    for i, p in enumerate((A3, C4, D4, E4)):
        t.note(i * Q, Q, p)

    # Bar 2: BEND - pick G4, bend up a whole step (to A4 pitch), hold, release
    s = bar
    t.note(s, H + Q, G4)
    if with_effects:
        for k in range(13):                               # bend up over an eighth+quarter
            t.bend(s + E + k * 30, 2 * k / 12)
        t.bend(s + H, 2)
        for k in range(13):                               # release back down
            t.bend(s + H + k * 15, 2 - 2 * k / 12)
    t.note(s + 3 * Q, Q, E4)

    # Bar 3: SLIDE - D4 slides up to A4 (7 frets) on the same string
    s = 2 * bar
    if with_effects:
        t.bend(s, 0)
        t.note(s, Q + E, D4)
        for k in range(16):                               # glide 7 semitones
            t.bend(s + E + k * 30, 7 * k / 15)
        t.bend(s + Q + E, 0)                              # reset before next note
        t.note(s + Q + E, H + E, A4)
    else:
        t.note(s, Q + E, D4)
        t.note(s + Q + E, H + E, A4)

    # Bar 4: VIBRATO - long A4 with 6 Hz pitch wobble
    s = 3 * bar
    t.note(s, bar, A4)
    if with_effects:
        ticks_per_sec = TPQ * 1_000_000 / TEMPO
        start, steps = s + Q, 60                          # wobble for the last 3 beats
        for k in range(steps + 1):
            tick = start + k * (3 * Q) // steps
            sec = (tick - start) / ticks_per_sec
            t.bend(tick, 0.4 * np.sin(2 * np.pi * 6 * sec))
        t.bend(s + bar, 0)

    # Bar 5: HAMMER-ON (C4 -> D4) and PULL-OFF (D4 -> C4), picked only once each
    s = 4 * bar
    soft = 70 if with_effects else 100                    # no pick attack = softer
    if with_effects:
        t.cc(s, 68, 127)                                  # legato on
    t.note(s, E, C4)
    t.note(s + E, E + Q, D4, soft)                        # hammer-on
    t.note(s + H, E, D4)
    t.note(s + H + E, E + Q, C4, soft)                    # pull-off
    if with_effects:
        t.cc(s + bar, 68, 0)                              # legato off

    # Bar 6: ending chord (A minor)
    s = 5 * bar
    for i, p in enumerate((A3, E4, A4, C4 + 12)):
        t.note(s + i * 20, bar, p, 90)                    # strummed: tiny delays
    return t


# =========================================================
# MIDI READER
# =========================================================

def read_midi(path):
    """Return notes [(start_s, end_s, pitch, velocity, channel)] and bends {ch: [(time_s, semis)]}."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"MThd":
        raise ValueError("Not a MIDI file")
    _, ntracks, division = struct.unpack(">HHH", data[8:14])
    pos, raw = 14, []

    for _ in range(ntracks):
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        p, end, tick, status = pos + 8, pos + 8 + length, 0, 0
        pos = end
        while p < end:
            delta = 0
            while True:
                b = data[p]
                p += 1
                delta = (delta << 7) | (b & 0x7F)
                if not b & 0x80:
                    break
            tick += delta
            if data[p] & 0x80:
                status = data[p]
                p += 1
            if status == 0xFF:                                       # meta event
                kind, n = data[p], data[p + 1]
                if kind == 0x51:
                    raw.append((tick, "tempo", int.from_bytes(data[p + 2:p + 5], "big")))
                p += 2 + n
            elif status in (0xF0, 0xF7):                             # sysex
                n = data[p]
                p += 1 + n
            else:
                size = 1 if status & 0xF0 in (0xC0, 0xD0) else 2     # running status supported
                raw.append((tick, "msg", (status,) + tuple(data[p:p + size])))
                p += size

    raw.sort(key=lambda e: e[0])
    bend_range = {}
    rpn = {}
    notes, bends, active = [], {}, {}
    sec, last_tick, tempo = 0.0, 0, 500000
    for tick, kind, val in raw:
        sec += (tick - last_tick) * tempo / 1e6 / division
        last_tick = tick
        if kind == "tempo":
            tempo = val
            continue
        st, *args = val
        ch, cmd = st & 0x0F, st & 0xF0
        if cmd == 0x90 and args[1] > 0:
            active[(ch, args[0])] = (sec, args[1])
        elif cmd in (0x80, 0x90):
            if (ch, args[0]) in active:
                start, vel = active.pop((ch, args[0]))
                notes.append((start, sec, args[0], vel, ch))
        elif cmd == 0xB0:
            rpn[(ch, args[0])] = args[1]
            if args[0] == 6 and rpn.get((ch, 101)) == 0 and rpn.get((ch, 100)) == 0:
                bend_range[ch] = args[1]
        elif cmd == 0xE0:
            value = args[0] | (args[1] << 7)
            bends.setdefault(ch, []).append((sec, (value - 8192) / 8192 * bend_range.get(ch, 2)))
    return notes, bends


# =========================================================
# SYNTHESIZER (MIDI -> WAV)
# =========================================================

def bend_curve(times, events):
    """Bend (semitones) at each time; holds the last value like a real synth."""
    if not events:
        return np.zeros_like(times)
    ev_t = np.array([e[0] for e in events])
    ev_v = np.array([e[1] for e in events])
    idx = np.searchsorted(ev_t, times, side="right") - 1
    return np.where(idx >= 0, ev_v[np.clip(idx, 0, None)], 0.0)


def render(notes, bends, path):
    length = max(n[1] for n in notes) + 1.5
    out = np.zeros(int(length * RATE))
    for start, end, pitch, vel, ch in notes:
        if ch == 9:                                    # skip drum channel
            continue
        dur = end - start + 0.6                        # let the string ring after note-off
        t = np.arange(int(dur * RATE)) / RATE
        semis = pitch - 69 + bend_curve(start + t, bends.get(ch, []))
        freq = 440 * 2 ** (semis / 12)
        phase = 2 * np.pi * np.cumsum(freq) / RATE
        tone = sum(np.sin(h * phase) * np.exp(-t * (1.5 + 1.2 * h)) / h for h in range(1, 7))
        release = np.clip((end + 0.6 - (start + t)) / 0.6, 0, 1)   # fade after note-off
        attack = np.clip(t / 0.004, 0, 1)
        i = int(start * RATE)
        out[i:i + len(t)] += tone * attack * release * vel / 127
    out = out / max(np.abs(out).max(), 1e-9) * 0.9
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    return out


def dominant_freq(signal, t0, t1):
    seg = signal[int(t0 * RATE):int(t1 * RATE)]
    spectrum = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n=1 << 17))
    return np.argmax(spectrum) * RATE / (1 << 17)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:                                     # convert user's file only
        src = sys.argv[1]
        dst = os.path.splitext(src)[0] + ".wav"
        render(*read_midi(src), dst)
        print(f"Converted {src} -> {dst}")
        sys.exit(0)

    for name, fx in (("sample", False), ("edited", True)):
        mid = os.path.join(here, name + ".mid")
        save_midi(mid, build(fx))
        notes, bends = read_midi(mid)
        audio = render(notes, bends, os.path.join(here, name + ".wav"))
        n_bends = sum(len(v) for v in bends.values())
        print(f"{name}.mid : {os.path.getsize(mid):5} bytes, {len(notes)} notes, {n_bends} pitch-bend messages")
        print(f"{name}.wav : {len(audio) / RATE:.1f} s, {RATE} Hz, 16-bit mono")

    # ---------- self-check: effects really change the sound ----------
    bar = 2.0                                                  # one bar = 2 s at 120 BPM
    with wave.open(os.path.join(here, "edited.wav")) as w:
        edited = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float)
    with wave.open(os.path.join(here, "sample.wav")) as w:
        sample = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float)

    f_plain = dominant_freq(sample, bar + 0.55, bar + 0.95)    # G4 held
    f_bent = dominant_freq(edited, bar + 0.55, bar + 0.95)     # G4 bent up 2 semitones
    print(f"\nBend check : plain {f_plain:.1f} Hz  ->  bent {f_bent:.1f} Hz "
          f"({12 * np.log2(f_bent / f_plain):+.2f} semitones, expected +2)")
    assert abs(12 * np.log2(f_bent / f_plain) - 2) < 0.15

    f_start = dominant_freq(edited, 2 * bar + 0.05, 2 * bar + 0.25)   # slide start (D4)
    f_end = dominant_freq(edited, 2 * bar + 0.70, 2 * bar + 0.74)     # slide top
    print(f"Slide check: {f_start:.1f} Hz  ->  {f_end:.1f} Hz "
          f"({12 * np.log2(f_end / f_start):+.2f} semitones, expected +7)")
    assert abs(12 * np.log2(f_end / f_start) - 7) < 0.6
    print("Self-check passed.")
