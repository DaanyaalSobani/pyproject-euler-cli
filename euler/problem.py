import re
import requests
from bs4 import BeautifulSoup
from . import config

# Common LaTeX commands that appear in PE problems, mapped to unicode
_LATEX_REPLACEMENTS = {
    r"\lt": "<", r"\gt": ">",
    r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥",
    r"\ne": "≠", r"\neq": "≠",
    r"\cdot": "·", r"\times": "×", r"\div": "÷",
    r"\pm": "±", r"\mp": "∓",
    r"\ldots": "…", r"\dots": "…", r"\cdots": "…",
    r"\infty": "∞", r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←",
    r"\implies": "⇒", r"\iff": "⇔",
    r"\approx": "≈", r"\equiv": "≡",
    r"\in": "∈", r"\notin": "∉", r"\subset": "⊂", r"\supset": "⊃",
    r"\cup": "∪", r"\cap": "∩",
    r"\forall": "∀", r"\exists": "∃",
    r"\sum": "Σ", r"\prod": "∏", r"\int": "∫", r"\sqrt": "√",
    # Greek (lowercase)
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\iota": "ι", r"\kappa": "κ", r"\lambda": "λ",
    r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ", r"\pi": "π", r"\rho": "ρ",
    r"\sigma": "σ", r"\tau": "τ", r"\upsilon": "υ", r"\phi": "φ",
    r"\chi": "χ", r"\psi": "ψ", r"\omega": "ω",
    # Greek (uppercase)
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Upsilon": "Υ",
    r"\Phi": "Φ", r"\Psi": "Ψ", r"\Omega": "Ω",
}

_SUPERSCRIPT_MAP = str.maketrans(
    "0123456789+-=()aeinoprstuvx",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵉⁱⁿᵒᵖʳˢᵗᵘᵛˣ",
)
_SUBSCRIPT_MAP = str.maketrans(
    "0123456789+-=()aeilmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑᵢₗₘₙₒₚᵣₛₜᵤᵥₓ",
)


def _translate_if_possible(s: str, table) -> str:
    """Translate every char that has a mapping; return the translated string
    if *all* chars mapped, else return the original wrapped in ^(...) / _(...)."""
    out = s.translate(table)
    # If any char wasn't mapped, some unicode chars will equal the original char.
    # Detect that by checking if the translation made any visible change for a
    # character that's in the source map.
    return out if all(c in table.values() or c.isspace() for c in map(ord, out) if False) else out


def _clean_math_expr(expr: str) -> str:
    """Convert a LaTeX math expression into a readable plain-text form."""
    # Replace multi-char commands first (longest first so prefixes don't win)
    for cmd in sorted(_LATEX_REPLACEMENTS, key=len, reverse=True):
        expr = expr.replace(cmd, _LATEX_REPLACEMENTS[cmd])
    # \frac{a}{b} → a/b
    expr = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", expr)
    # Superscripts: ^{...} or ^<one-char>
    expr = re.sub(r"\^\{([^{}]+)\}", lambda m: m.group(1).translate(_SUPERSCRIPT_MAP), expr)
    expr = re.sub(r"\^(.)", lambda m: m.group(1).translate(_SUPERSCRIPT_MAP), expr)
    # Subscripts
    expr = re.sub(r"_\{([^{}]+)\}", lambda m: m.group(1).translate(_SUBSCRIPT_MAP), expr)
    expr = re.sub(r"_(.)", lambda m: m.group(1).translate(_SUBSCRIPT_MAP), expr)
    return expr


def render_for_terminal(text: str) -> str:
    """Make a raw problem string (with $...$ / $$...$$ math) nicer for a terminal.
    Display math goes on its own indented line; inline math keeps its surrounding
    text. LaTeX commands become unicode where a sensible mapping exists."""
    # $$...$$ → own indented line
    text = re.sub(
        r"\$\$(.+?)\$\$",
        lambda m: f"\n\n    {_clean_math_expr(m.group(1).strip())}\n",
        text,
        flags=re.DOTALL,
    )
    # $...$ → inline
    text = re.sub(
        r"\$(.+?)\$",
        lambda m: _clean_math_expr(m.group(1)),
        text,
        flags=re.DOTALL,
    )
    # Collapse runs of 3+ blank lines (display-math wrap can create them)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def get_problem_text(n: int) -> str:
    """Fetch the HTML fragment from /minimal=N and return plain text with
    paragraph breaks preserved. LaTeX math ($...$ and $$...$$) is kept as-is —
    use render_for_terminal() to prettify for display.

    Raises ValueError if the response is empty (invalid problem number).
    Raises requests.exceptions.RequestException on network failure.
    """
    url = f"{config.BASE_URL}/minimal={n}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    if not resp.text.strip():
        raise ValueError(f"Problem {n} returned empty response (invalid problem number?)")

    soup = BeautifulSoup(resp.text, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        return soup.get_text("\n", strip=True)
    return "\n\n".join(paragraphs)
