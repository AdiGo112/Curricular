# Assignment 3: MIDI File with Guitar Effects, Converted to WAV

## Files

| File | Description |
| --- | --- |
| `sample.mid` | Plain 6-bar guitar riff (A minor pentatonic), 120 BPM |
| `edited.mid` | Same riff with bend, slide, vibrato, hammer-on and pull-off |
| `sample.wav`, `edited.wav` | Both MIDI files converted to 16-bit WAV |
| `midi_effects.py` | Creates the MIDI files byte by byte, reads them back and renders WAV |

```bash
pip install numpy
python midi_effects.py            # create both .mid and .wav files, then self-check
python midi_effects.py song.mid   # convert any MIDI file to WAV
```

## How Each Effect is Stored in MIDI

| Bar | Effect | MIDI messages used |
| --- | --- | --- |
| 1 | Plain notes | Note On / Note Off |
| 2 | **Bend** | Pitch Bend rising from 0 to +2 semitones, held, then released to 0 |
| 3 | **Slide** | Pitch Bend gliding 0 → +7 semitones (D4 to A4), then the target note |
| 4 | **Vibrato** | 60 Pitch Bend messages making a ±0.4-semitone sine wave at 6 Hz |
| 5 | **Hammer-on / Pull-off** | Second note with lower velocity (70 instead of 100, no pick attack) and Legato pedal CC 68 on/off |
| 6 | Strummed chord | Notes starting 20 ticks apart |

At the start of the track, **RPN 0** (CC 101/100 = 0, then CC 6 = 12) sets the pitch-bend range to 12 semitones, so a 7-semitone slide fits.

The self-check measures the rendered audio: the bend comes out at **+2.00 semitones** and the slide at **+6.8 semitones**.

## Doing the Same in the GUI Tools

### TuxGuitar (best for guitar effects)
1. **File → Open** `sample.mid`.
2. Select a note, then open **Effects**:
   - **Bend** (choose "Bend" or "Bend and Release")
   - **Slide** (select the first note of the slide)
   - **Vibrato**
   - **Hammer-on / Pull-off** (select the first note of the pair)
3. **File → Export → Export Audio File** and choose WAV. Or export MIDI, then convert in LMMS.

### MuseScore
1. **File → Open** `sample.mid`.
2. Palettes → **Arpeggios & Glissandi** (slide), **Ornaments** (vibrato), **Bend** for a guitar bend, **Slur** for hammer-on/pull-off.
3. **File → Export → WAV Audio**.

### LMMS
1. **Project → Import** `edited.mid` (the guitar track uses the GM sound font).
2. Press Play to hear it. The pitch-bend automation shows up in the Automation Editor.
3. **Project → Export** and choose **WAV**.
