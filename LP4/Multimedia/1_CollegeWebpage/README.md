# Assignment 1: Open-Source Multimedia Tools and a College Webpage

## Part A: Study of Open-Source Multimedia Tools

Open-source software can be used, studied, changed and shared for free. These tools cover all the media types used in multimedia: text, image, audio, video, animation and 3D.

| Media | Tool | What it is used for | Licence | Install (Linux) | Download (Windows) |
| --- | --- | --- | --- | --- | --- |
| Raster images | **GIMP** | Photo editing, layers, filters, banners | GPL | `sudo apt install gimp` | gimp.org |
| Raster painting | **Krita** | Digital painting, textures | GPL | `sudo apt install krita` | krita.org |
| Vector graphics | **Inkscape** | Logos, icons, SVG illustrations | GPL | `sudo apt install inkscape` | inkscape.org |
| Audio editing | **Audacity** | Recording, cutting, noise removal, effects | GPL | `sudo apt install audacity` | audacityteam.org |
| Music / MIDI | **LMMS** | Beat making, MIDI sequencing, export WAV | GPL | `sudo apt install lmms` | lmms.io |
| Music notation | **MuseScore** | Sheet music, MIDI import/export | GPL | `sudo apt install musescore3` | musescore.org |
| Video editing | **Shotcut** / **Kdenlive** | Cutting, transitions, titles | GPL | `sudo apt install kdenlive` | shotcut.org / kdenlive.org |
| Screen recording | **OBS Studio** | Recording and live streaming | GPL | `sudo apt install obs-studio` | obsproject.com |
| Conversion | **FFmpeg** / **HandBrake** | Convert audio/video formats | LGPL/GPL | `sudo apt install ffmpeg handbrake` | ffmpeg.org / handbrake.fr |
| Media player | **VLC** | Plays almost every format | GPL/LGPL | `sudo apt install vlc` | videolan.org |
| 3D / animation | **Blender** | Modelling, animation, rendering | GPL | `sudo apt install blender` | blender.org |
| Web authoring | **VS Code** (MIT core) / **Bluefish** | Writing HTML, CSS, JS | MIT / GPL | `sudo apt install bluefish` | code.visualstudio.com |

### Installation Steps (Windows, example: GIMP)
1. Open https://www.gimp.org/downloads and download the installer.
2. Run the `.exe`, choose **Install for all users**, and keep the default components.
3. Open GIMP from the Start menu, then **File → New** to check it works.

The same steps work for the other tools. On Linux, use the `apt` command in the table.

## Part B: College Webpage

**Files:** `index.html`, `style.css`, `logo.svg`. Open `index.html` in a browser.

| Tool | How it was used |
| --- | --- |
| **Inkscape** | College logo designed as vector graphics and saved as `logo.svg`. It stays sharp at any size and is also used as the browser tab icon |
| **GIMP** | (Optional) Export a JPEG/PNG banner or campus photos and put them in the gallery |
| **VS Code / Bluefish** | Wrote the HTML structure and CSS styling |
| **Browser (Chrome / Firefox)** | Tested the layout at desktop and phone widths |

### Page Sections
Header with logo and navigation → Hero banner (SVG campus illustration) → About with key statistics → Departments → Admissions table → Notice board → Campus gallery → Contact → Footer.

### Web Features Used
- Semantic HTML5: `header`, `nav`, `section`, `article`, `figure`, `time`
- SVG graphics, inline and as a file
- CSS Grid and Flexbox for a responsive layout (works on phones)
- Sticky navigation bar with smooth scrolling to sections
- CSS custom properties (variables) for the colour theme

To use it for your own college, replace "Sunrise Institute of Technology" and the details with your college's information.
