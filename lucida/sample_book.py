from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


W, H = letter  # 612 x 792
INK = (0.07, 0.06, 0.05)
RUST = (0.62, 0.28, 0.16)
RULE = (0.62, 0.28, 0.16)
DIM = (0.28, 0.25, 0.22)
CREAM = (0.965, 0.945, 0.90)

DISPLAY = "Times-Bold"
BODY = "Times-Roman"
BODYI = "Times-Italic"


def ensure_sample(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 2000:
        return path
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setTitle("STARFORGE — A pocket atlas of stellar engines")
    c.setAuthor("LUCIDA field notes")
    c.setSubject("A sample book for the Lucida holodeck")
    _p1(c)
    _p2(c)
    _p3(c)
    _p4(c)
    _p5(c)
    _p6(c)
    _p7(c)
    _p8(c)
    c.save()
    return path



def _bg(c: canvas.Canvas) -> None:
    c.setFillColorRGB(*CREAM)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _footer(c: canvas.Canvas, n: int, label: str) -> None:
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.4)
    c.line(54, 42, W - 54, 42)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 8)
    c.drawString(54, 28, f"CH.{n:02d}")
    c.drawRightString(W - 54, 28, label)
    c.showPage()


def _rule(c: canvas.Canvas, y: float) -> None:
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.6)
    c.line(54, y, W - 54, y)


def _wrap(c: canvas.Canvas, text: str, font: str, size: float, max_w: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if c.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _body(c: canvas.Canvas, text: str, x: float, y: float, max_w: float, leading: float = 15) -> float:
    c.setFillColorRGB(*INK)
    c.setFont(BODY, 11)
    for line in _wrap(c, text, BODY, 11, max_w):
        c.drawString(x, y, line)
        y -= leading
    return y


def _p1(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "FIELD NOTES  ·  VOLUME I")
    _rule(c, H - 76)
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 42)
    c.drawString(54, H - 170, "STARFORGE")
    c.setFont(BODYI, 16)
    c.drawString(54, H - 202, "A pocket atlas of stellar engines")
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(1.1)
    c.line(54, H - 230, 220, H - 230)
    quote = "A star is a machine that burns time into light."
    c.setFont(BODYI, 13)
    c.setFillColorRGB(*INK)
    y = H - 290
    for line in _wrap(c, quote, BODYI, 13, 420):
        c.drawString(54, y, line)
        y -= 18
    c.setFont(BODY, 10)
    c.setFillColorRGB(*DIM)
    c.drawString(54, 96, "Eight chambers. One page each. Walk them in order.")
    _footer(c, 1, "STARFORGE")


def _p2(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "INSTRUMENTS")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "How to walk a chamber")
    _rule(c, H - 122)
    y = _body(
        c,
        "This atlas is not a story you finish. It is a hall of rooms. Each page is one engine, "
        "cut open and lit from the inside. You do not skim. You stand in the room until the "
        "machine makes sense, then you step through the wall into the next.",
        54,
        H - 160,
        504,
    )
    y -= 18
    y = _body(
        c,
        "Four instruments hang on every wall: mass, which sets the appetite of the fire; light, "
        "which is the waste heat of that appetite; color, which is a temperature you can see; "
        "and time, which is how long the fuel can last. Read them as a set. A number alone is a "
        "souvenir. Four numbers are a diagnosis.",
        54,
        y,
        504,
    )
    y -= 28
    c.setFont(DISPLAY, 13)
    c.setFillColorRGB(*INK)
    c.drawString(54, y, "The four instruments")
    y -= 18
    rows = [
        ("MASS", "How much matter the engine can crush. Unit: solar masses."),
        ("LIGHT", "Power poured into space. Unit: solar luminosities."),
        ("COLOR", "Surface temperature, written as spectral class O through M."),
        ("TIME", "Main-sequence lifetime. Heavy stars spend their fortune fast."),
    ]
    for name, blurb in rows:
        c.setFillColorRGB(*RUST)
        c.setFont(BODY, 9)
        c.drawString(54, y, name)
        c.setFillColorRGB(*INK)
        c.setFont(BODY, 11)
        c.drawString(140, y, blurb)
        y -= 22
    _footer(c, 2, "INSTRUMENTS")


def _p3(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "LEDGER")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "The mass–luminosity ledger")
    _rule(c, H - 122)
    y = _body(
        c,
        "Double a star's mass and you do not double its light. You multiply it. The engine is "
        "nonlinear: core pressure climbs, fusion rate explodes, and the surface becomes a furnace "
        "that cannot be sustained for long. This table is the whole argument in six rows.",
        54,
        H - 158,
        504,
    )
    headers = ["Class", "Mass (☉)", "Luminosity (☉)", "Lifetime (yr)", "Temp (K)"]
    rows = [
        ["O5", "40", "400000", "1,000,000", "40000"],
        ["B0", "17", "20000", "10,000,000", "25000"],
        ["A0", "2.7", "55", "400,000,000", "9500"],
        ["G2 (Sun)", "1.0", "1", "10,000,000,000", "5772"],
        ["K5", "0.67", "0.17", "30,000,000,000", "4400"],
        ["M0", "0.51", "0.08", "70,000,000,000", "3800"],
    ]
    table_top = y - 36
    cols = [54, 130, 220, 330, 460]
    c.setFont(BODY, 8)
    c.setFillColorRGB(*RUST)
    for x, h in zip(cols, headers):
        c.drawString(x, table_top, h)
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.5)
    c.line(54, table_top - 8, W - 54, table_top - 8)
    c.setFillColorRGB(*INK)
    c.setFont(BODY, 10)
    yy = table_top - 28
    for row in rows:
        for x, cell in zip(cols, row):
            c.drawString(x, yy, cell)
        yy -= 22
    y = _body(
        c,
        "Read the last two columns against each other. Forty thousand kelvin costs a million years. "
        "Thirty-eight hundred kelvin buys seventy billion. The sky is full of thrifty red engines "
        "because the spendthrifts have already left.",
        54,
        yy - 16,
        504,
    )
    _footer(c, 3, "LEDGER")


def _p4(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "CORE")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "The boiling core")
    _rule(c, H - 122)
    y = _body(
        c,
        "Fifteen million kelvin is not a metaphor. It is the temperature at which hydrogen nuclei "
        "move fast enough to tunnel through their own repulsion and become helium. In the Sun this "
        "happens in a core about 0.2 solar radii across, under a density of 150 grams per cubic "
        "centimeter — more like white-hot metal than gas.",
        54,
        H - 158,
        504,
    )
    y -= 10
    y = _body(
        c,
        "Energy does not beam out. Photons are born as gamma rays and then play a three-dimensional "
        "drunkard's walk through the radiative zone, colliding for about 100,000 years before they "
        "reach the convective envelope. What you see as sunlight is a delayed letter from the deep "
        "past of the core.",
        54,
        y,
        504,
    )
    y -= 22
    facts = [
        ("Core temperature", "15,000,000 K"),
        ("Core density", "150 g/cm³"),
        ("Photon random-walk", "100,000 years"),
        ("Neutrino escape", "2.3 seconds"),
        ("Hydrogen fused / sec", "620,000,000 tons"),
        ("Mass lost as light / sec", "4,300,000 tons"),
    ]
    c.setFont(DISPLAY, 12)
    c.setFillColorRGB(*INK)
    c.drawString(54, y, "Sun-as-engine, present tense")
    y -= 20
    for label, val in facts:
        c.setFillColorRGB(*DIM)
        c.setFont(BODY, 10)
        c.drawString(54, y, label)
        c.setFillColorRGB(*INK)
        c.setFont(BODY, 11)
        c.drawRightString(W - 54, y, val)
        y -= 18
    y -= 8
    _body(
        c,
        "Neutrinos skip the drunkard's walk. They leave the core in 2.3 seconds and pass through "
        "the Earth at night as if the planet were a rumor. A star is therefore two clocks at once: "
        "a slow clock of light, and a fast clock of ghosts.",
        54,
        y,
        504,
    )
    _footer(c, 4, "CORE")


def _p5(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "SPECIMENS")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "Spectral engines")
    _rule(c, H - 122)
    y = _body(
        c,
        "Annie Jump Cannon sorted the sky into a temperature ladder: O B A F G K M. The mnemonic "
        "is a joke. The science is a thermometer you can hang on a spectrum. Blue-white is hungry. "
        "Red is patient. The Sun is a G2, which is to say a yellow-white moderate, neither miser "
        "nor spendthrift.",
        54,
        H - 158,
        504,
    )
    headers = ["Class", "Color", "Temp (K)", "Example", "Fate"]
    rows = [
        ["O", "blue-white", "30000–50000", "Alnitak", "core collapse"],
        ["B", "blue", "10000–30000", "Rigel", "core collapse"],
        ["A", "white", "7500–10000", "Sirius", "white dwarf"],
        ["F", "yellow-white", "6000–7500", "Procyon", "white dwarf"],
        ["G", "yellow", "5200–6000", "the Sun", "white dwarf"],
        ["K", "orange", "3700–5200", "Arcturus", "white dwarf"],
        ["M", "red", "2400–3700", "Proxima", "long fade"],
    ]
    table_top = y - 32
    cols = [54, 120, 210, 330, 430]
    c.setFont(BODY, 8)
    c.setFillColorRGB(*RUST)
    for x, h in zip(cols, headers):
        c.drawString(x, table_top, h)
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.5)
    c.line(54, table_top - 8, W - 54, table_top - 8)
    c.setFillColorRGB(*INK)
    c.setFont(BODY, 10)
    yy = table_top - 26
    for row in rows:
        for x, cell in zip(cols, row):
            c.drawString(x, yy, cell)
        yy -= 20
    _body(
        c,
        "Only O and B stars die as collapses that can mint neutron stars or black holes. Everything "
        "cooler than about 8 solar masses will one day be a white dwarf: an Earth-sized ember of "
        "degenerate carbon, cooling for longer than the universe has so far lasted.",
        54,
        yy - 12,
        504,
    )
    _footer(c, 5, "SPECIMENS")


def _p6(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "GHOSTS")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "A census of neutrinos")
    _rule(c, H - 122)
    y = _body(
        c,
        "Every second, about 65 billion solar neutrinos pass through each square centimeter of your "
        "body. They are not a weather. They are a correspondence. Most were written 8.3 minutes ago "
        "in the proton–proton chain; a few are fossils from supernovae and the big bang.",
        54,
        H - 158,
        504,
    )
    y -= 12
    facts = [
        ("Solar neutrinos through a fingernail / sec", "65,000,000,000"),
        ("Time to cross the Sun from core", "2.3 seconds"),
        ("Time for light to do the same", "100,000 years"),
        ("Earth as neutrino shield", "effectively transparent"),
        ("Supernova 1987A neutrinos detected", "25"),
        ("Rest mass", "< 0.8 eV"),
    ]
    for label, val in facts:
        c.setFillColorRGB(*DIM)
        c.setFont(BODY, 10)
        c.drawString(54, y, label)
        c.setFillColorRGB(*INK)
        c.setFont(BODY, 11)
        c.drawRightString(W - 54, y, val)
        y -= 20
    y -= 8
    _body(
        c,
        "In 1987, twenty-five neutrinos arrived from a star that died in the Large Magellanic Cloud "
        "160,000 years earlier. They came three hours before the light. That is the holodeck trick "
        "the universe already performs: the ghost of an engine reaches you before the picture does.",
        54,
        y,
        504,
    )
    _footer(c, 6, "GHOSTS")


def _p7(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "ENDING")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "The giant's last ledger")
    _rule(c, H - 122)
    y = _body(
        c,
        "When core hydrogen is gone, the engine does not politely stop. The core contracts, shell "
        "burning ignites, and the envelope inflates into a red giant. For a Sun-like star the "
        "sequence is a timetable, not a mystery.",
        54,
        H - 158,
        504,
    )
    headers = ["Stage", "Year offset", "Radius (☉)", "Luminosity (☉)", "Note"]
    rows = [
        ["main sequence now", "0", "1", "1", "core H fusion"],
        ["subgiant", "+5.4e9", "2.3", "2.2", "H shell ignites"],
        ["red giant branch", "+7.1e9", "150", "2000", "core helium ash"],
        ["helium flash", "+7.7e9", "10", "50", "core He ignition"],
        ["horizontal branch", "+7.8e9", "10", "50", "quiet He burning"],
        ["AGB pulse", "+8.0e9", "200", "3000", "shells double"],
        ["planetary nebula", "+8.1e9", "—", "—", "envelope ejected"],
        ["white dwarf", "+8.2e9", "0.01", "0.001", "Earth-sized ember"],
    ]
    table_top = y - 28
    cols = [54, 168, 250, 330, 420]
    c.setFont(BODY, 7.5)
    c.setFillColorRGB(*RUST)
    for x, h in zip(cols, headers):
        c.drawString(x, table_top, h)
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.5)
    c.line(54, table_top - 8, W - 54, table_top - 8)
    c.setFillColorRGB(*INK)
    c.setFont(BODY, 9)
    yy = table_top - 24
    for row in rows:
        for x, cell in zip(cols, row):
            c.drawString(x, yy, cell)
        yy -= 18
    _body(
        c,
        "The red giant the Sun becomes will swallow Mercury and Venus and may lick the Earth. Then "
        "it will shrug off its atmosphere as a planetary nebula — a poor name for a rich event — "
        "and leave a white dwarf of about 0.54 solar masses. That ember is the original engine, "
        "retired, still hot, no longer employed.",
        54,
        yy - 10,
        504,
    )
    _footer(c, 7, "ENDING")


def _p8(c: canvas.Canvas) -> None:
    _bg(c)
    c.setFillColorRGB(*RUST)
    c.setFont(BODY, 9)
    c.drawString(54, H - 64, "CODA")
    c.setFillColorRGB(*INK)
    c.setFont(DISPLAY, 22)
    c.drawString(54, H - 108, "The sky is a machine")
    _rule(c, H - 122)
    y = _body(
        c,
        "Walk back through the chambers and the night stops being a decoration. Every naked-eye "
        "star is an engine whose ledger you can now roughly guess: color is temperature, brightness "
        "plus distance is power, power plus mass is a lifetime. The constellations are not stories. "
        "They are a shop floor.",
        54,
        H - 158,
        504,
    )
    y -= 12
    y = _body(
        c,
        "You do not need a telescope to begin. You need the habit of treating a page as a room. "
        "Stand in it. Let the numbers become objects. When the next page opens, the previous room "
        "goes dark behind you, the way a holodeck does, and the new engine takes the floor.",
        54,
        y,
        504,
    )
    y -= 28
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.8)
    c.line(54, y, 200, y)
    y -= 28
    c.setFont(BODYI, 13)
    c.setFillColorRGB(*INK)
    for line in _wrap(c, "Close the book. Look up. The machines are still on.", BODYI, 13, 500):
        c.drawString(54, y, line)
        y -= 18
    c.setFont(BODY, 9)
    c.setFillColorRGB(*DIM)
    c.drawString(54, 96, "End of volume I  ·  drop another book to raise a new hall")
    _footer(c, 8, "CODA")
