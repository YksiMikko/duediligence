"""
Valuatum Due Diligence & Neuvotteluapuri
==========================================
Yhden tiedoston Streamlit-sovellus, joka ottaa syötteenä yrityksen keskeiset
talousluvut ja tuottaa Google Gemini -mallin (gemini-2.5-flash) avulla
strukturoidun (Pydantic / JSON-skeema) tarkastuslistan yrityskauppa- tai
luottoneuvotteluja varten.

Käynnistys:
    streamlit run app.py

API-avain haetaan tässä järjestyksessä:
    1. Sivupalkin syöttökenttä (jos käyttäjä syöttää sen käsin)
    2. st.secrets["GEMINI_API_KEY"]
    3. os.environ["GEMINI_API_KEY"]

Riippuvuudet (myös requirements.txt-tiedostossa tämän tiedoston vieressä):
    streamlit
    google-genai
    pydantic
"""

from __future__ import annotations

import json
import os
from enum import Enum
from typing import List, Optional

import streamlit as st
from pydantic import BaseModel, Field

from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Perusasetukset
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Valuatum Due Diligence & Neuvotteluapuri",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Valuatum-bränditeema (väripaletti, typografia, hero) — valuatum.fi-tyylinen
# ---------------------------------------------------------------------------

VALUATUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
    --vt-bg:            #0B1D17;
    --vt-bg-2:          #0E2019;
    --vt-panel:         #12261F;
    --vt-panel-2:       #16302677;
    --vt-lime:          #9AD13A;
    --vt-lime-soft:     #C4E88F;
    --vt-btn-1:         #3FA86A;
    --vt-btn-2:         #1E6B45;
    --vt-border:        rgba(255,255,255,0.12);
    --vt-white:         #FFFFFF;
    --vt-muted:         #A9BDB3;
}

html, body, [class*="css"], .stApp{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp{
    background:
        radial-gradient(1100px 480px at 12% -10%, #123527 0%, transparent 60%),
        radial-gradient(900px 420px at 100% 0%, #0f2a20 0%, transparent 55%),
        linear-gradient(180deg, var(--vt-bg) 0%, var(--vt-bg-2) 100%) !important;
    color: var(--vt-white);
}

section[data-testid="stSidebar"]{
    background: #081712 !important;
    border-right: 1px solid var(--vt-border);
}
section[data-testid="stSidebar"] * { color: var(--vt-white) !important; }
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small{
    color: var(--vt-muted) !important;
}

h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3{
    color: var(--vt-white) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}

p, span, label, .stMarkdown, .stCaption{
    color: var(--vt-muted);
}

/* --- Hero-osio, joka toistaa valuatum.fi:n etusivun rakenteen --- */
.vt-hero{
    margin: -1rem -1rem 2rem -1rem;
    padding: 1.4rem 2.5rem 2.6rem 2.5rem;
    background:
        repeating-linear-gradient(100deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 90px),
        radial-gradient(700px 260px at 50% 0%, rgba(154,209,58,0.08) 0%, transparent 70%),
        linear-gradient(180deg, #0c231b 0%, #0a1c15 100%);
    border-bottom: 1px solid var(--vt-border);
    text-align: center;
}
.vt-nav{
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1100px;
    margin: 0 auto 2.4rem auto;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.vt-logo{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 800;
    font-size: 1.15rem;
    color: var(--vt-white);
}
.vt-logo svg{ display:block; }
.vt-nav-badge{
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--vt-bg);
    background: linear-gradient(135deg, var(--vt-lime-soft), var(--vt-lime));
    padding: 0.4rem 1rem;
    border-radius: 999px;
}
.vt-eyebrow{
    color: var(--vt-lime);
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
}
.vt-hero h1{
    font-size: 2.7rem;
    line-height: 1.15;
    font-weight: 800;
    color: var(--vt-white);
    max-width: 780px;
    margin: 0 auto 1rem auto;
}
.vt-hero p{
    max-width: 620px;
    margin: 0 auto;
    color: var(--vt-muted);
    font-size: 1.02rem;
    line-height: 1.6;
}

/* --- Napit pill-muotoisina kuten valuatum.fi:n CTA:t --- */
div.stButton > button, div.stDownloadButton > button{
    background: linear-gradient(135deg, var(--vt-btn-1), var(--vt-btn-2)) !important;
    color: var(--vt-white) !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.65rem 1.6rem !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 18px rgba(31,107,69,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover{
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(31,107,69,0.45);
}
section[data-testid="stSidebar"] div.stButton > button{
    background: transparent !important;
    border: 1px solid var(--vt-lime) !important;
    color: var(--vt-lime) !important;
    box-shadow: none;
}
section[data-testid="stSidebar"] div.stButton > button:hover{
    background: rgba(154,209,58,0.1) !important;
}

/* --- Syöttökentät tumman teeman mukaisiksi --- */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div{
    background-color: var(--vt-panel) !important;
    color: var(--vt-white) !important;
    border: 1px solid var(--vt-border) !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus{
    border-color: var(--vt-lime) !important;
    box-shadow: 0 0 0 1px var(--vt-lime) !important;
}
.stSelectbox svg{ fill: var(--vt-white) !important; }

/* --- Info-laatikko, expanderit, metriikat --- */
div[data-testid="stAlert"]{
    background: var(--vt-panel-2) !important;
    border: 1px solid var(--vt-border) !important;
    border-left: 4px solid var(--vt-lime) !important;
    color: var(--vt-white) !important;
    border-radius: 10px !important;
}
div[data-testid="stAlert"] p{ color: var(--vt-white) !important; }

details, .streamlit-expanderHeader{
    background: var(--vt-panel) !important;
    border: 1px solid var(--vt-border) !important;
    border-radius: 10px !important;
    color: var(--vt-white) !important;
}
.streamlit-expanderHeader p{ color: var(--vt-white) !important; font-weight: 600; }
.streamlit-expanderContent{
    background: var(--vt-bg-2) !important;
    border: 1px solid var(--vt-border) !important;
    border-top: none !important;
}

div[data-testid="stMetric"]{
    background: var(--vt-panel);
    border: 1px solid var(--vt-border);
    border-radius: 12px;
    padding: 0.9rem 1rem;
}
div[data-testid="stMetricValue"]{ color: var(--vt-white) !important; }
div[data-testid="stMetricLabel"]{ color: var(--vt-muted) !important; }

hr, div[data-testid="stDivider"]{ border-color: var(--vt-border) !important; }
</style>
"""

VALUATUM_LOGO_SVG = """
<svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M2 13 L15 4 L11 13 L15 22 Z" fill="#9AD13A"/>
</svg>
"""

st.markdown(VALUATUM_CSS, unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="vt-hero">
        <div class="vt-nav">
            <div class="vt-logo">{VALUATUM_LOGO_SVG} Valuatum</div>
            <div class="vt-nav-badge">Due Diligence -työkalu</div>
        </div>
        <div class="vt-eyebrow">Financial Analysis Solutions</div>
        <h1>Selkeyttä jokaiseen<br>luotto- ja kauppaneuvotteluun.</h1>
        <p>
            Syötä kohdeyrityksen keskeiset talousluvut ja saat tekoälyn avustuksella
            jäsennellyn due diligence -tarkastuslistan neuvottelua varten.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


MODEL_NAME = "gemini-2.5-flash"
CREDIT_RATINGS = ["AAA", "AA", "A", "B", "C"]

DEFAULT_VALUES = {
    "company_name": "",
    "industry": "",
    "credit_rating": "A",
    "revenue": 0.0,
    "revenue_change": 0.0,
    "ebit_margin": 0.0,
    "quick_ratio": 0.0,
    "equity_ratio": 0.0,
    "dso_days": 0.0,
    "notes": "",
}

# Esimerkkidata: teollisuusyritys, liikevaihto kasvaa mutta kassa kuivuu
EXAMPLE_VALUES = {
    "company_name": "Nordic Metalworks Oy",
    "industry": "Teollisuus – metallien koneistus ja alihankinta",
    "credit_rating": "B",
    "revenue": 18_500_000.0,
    "revenue_change": 22.0,
    "ebit_margin": 4.1,
    "quick_ratio": 0.6,
    "equity_ratio": 21.0,
    "dso_days": 78.0,
    "notes": (
        "Johto perustelee kasvua uudella isolla asiakassopimuksella. "
        "Investointeja koneisiin tehty velkarahalla viimeisen 12kk aikana. "
        "Muutama suurimmista asiakassaatavista on erääntynyt yli 90 päivää. "
        "Johto vakuuttaa kassavirran korjaantuvan Q3-Q4 aikana."
    ),
}


# ---------------------------------------------------------------------------
# Pydantic-mallit strukturoitua Gemini-tulostusta varten
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    KRIITTINEN = "KRIITTINEN"
    KOHTALAINEN = "KOHTALAINEN"
    HUOMIOITAVA = "HUOMIOITAVA"


class RedFlag(BaseModel):
    title: str = Field(description="Lyhyt otsikko havaitulle riskille tai ristiriidalle")
    severity: Severity = Field(description="Riskin vakavuus")
    explanation: str = Field(description="Perustelu: miksi tämä on riski ja mihin lukuihin se perustuu")


class ManagementQuestion(BaseModel):
    topic: str = Field(description="Aihealue, johon kysymys liittyy (esim. Kassavirta, Saatavat)")
    question: str = Field(description="Konkreettinen kysymys, joka esitetään johdolle")
    what_to_look_for: str = Field(description="Mitä vastauksessa kannattaa tarkkailla tai mikä olisi huolestuttava vastaus")


class AnalysisResult(BaseModel):
    overall_risk_summary: str = Field(description="2-3 lauseen tiivistelmä kokonaistilanteesta ja -riskistä")
    red_flags: List[RedFlag] = Field(description="Havaitut riskit ja ristiriidat vakavuusjärjestyksessä")
    questions_for_management: List[ManagementQuestion] = Field(description="Kysymykset johdolle / toimitusjohtajalle")
    recommended_actions: List[str] = Field(description="Konkreettiset suositellut sopimusehdot tai toimenpiteet")


# ---------------------------------------------------------------------------
# Session state -alustus
# ---------------------------------------------------------------------------

def init_state():
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "analysis_result" not in st.session_state:
        st.session_state["analysis_result"] = None
    if "manual_api_key" not in st.session_state:
        st.session_state["manual_api_key"] = ""


def load_example_data():
    """Täyttää lomakkeen esimerkkiyrityksen luvuilla."""
    for key, value in EXAMPLE_VALUES.items():
        st.session_state[key] = value


init_state()


# ---------------------------------------------------------------------------
# API-avaimen resolvointi
# ---------------------------------------------------------------------------

def resolve_api_key(manual_key: str) -> Optional[str]:
    """Palauttaa API-avaimen prioriteettijärjestyksessä:
    1) käyttäjän syöttämä avain
    2) st.secrets
    3) ympäristömuuttuja
    """
    if manual_key:
        return manual_key.strip()

    try:
        secret_key = st.secrets["GEMINI_API_KEY"]
        if secret_key:
            return secret_key
    except Exception:
        pass

    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key

    return None


# ---------------------------------------------------------------------------
# Prompti ja Gemini-kutsu
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """\
Olet "Valuatum" – kokenut senior-analyytikko, joka on erikoistunut yritysjärjestelyiden \
(M&A) due diligence -tarkastuksiin ja luottoriskianalyysiin. Autat neuvottelijaa \
(esim. pankin luottoanalyytikko tai ostajan due diligence -tiimi) valmistautumaan \
neuvotteluun kohdeyrityksen kanssa.

Kirjoita selkeällä, asiallisella suomen kielellä ilman turhaa jargonia. Ole \
konkreettinen ja perustele havaintosi aina annetuilla luvuilla.

Analysoi annetut talousluvut kriittisesti ja tunnista erityisesti:
- ristiriidat eri tunnuslukujen välillä (esim. kasvava liikevaihto mutta \
  heikkenevä maksuvalmius)
- likviditeetti- ja kassavirtariskit
- velkaantumis- ja vakavaraisuusriskit
- kannattavuuden laatu (onko kasvu kannattavaa)
- myyntisaamisten kiertoajan ja luottoriskin yhteys
- mahdolliset "red flag" -signaalit, jotka kaipaavat lisäselvitystä

Ota huomioon yrityksen toimiala ja Valuatumin antama luottoluokka kontekstina \
riskitason arvioinnissa – matalampi luottoluokka (B, C) tarkoittaa, että \
analyysin ja kysymyslistan tulee olla tiukempi ja yksityiskohtaisempi.

Käytä annettuja "muita huomioita / johdon kommentteja" arvioidaksesi, ovatko \
johdon selitykset uskottavia vai vaativatko ne lisänäyttöä.

Palauta vastauksesi TÄSMÄLLEEN annetun JSON-skeeman mukaisessa muodossa. \
Älä keksi lukuja, joita käyttäjä ei ole antanut – jos jokin tieto puuttuu, \
muotoile se selvitettävänä asiana kysymyslistalle.
"""


def build_user_prompt(data: dict) -> str:
    notes = data["notes"].strip() or "Ei erillisiä huomioita annettu."
    return f"""\
Analysoi seuraava kohdeyritys ja tuota due diligence- ja neuvottelutarkastuslista.

## Yrityksen perustiedot
- Nimi: {data['company_name'] or "Ei annettu"}
- Toimiala: {data['industry'] or "Ei annettu"}
- Valuatumin luottoluokka: {data['credit_rating']}

## Talousluvut
- Liikevaihto: {data['revenue']:,.0f} €
- Liikevaihdon muutos: {data['revenue_change']:.1f} %
- Liiketulos / EBIT-%: {data['ebit_margin']:.1f} %
- Quick ratio: {data['quick_ratio']:.2f}
- Omavaraisuusaste: {data['equity_ratio']:.1f} %
- Myyntisaamisten kiertoaika: {data['dso_days']:.0f} päivää

## Muut huomiot / johdon kommentit
{notes}
"""


def call_gemini(api_key: str, data: dict) -> AnalysisResult:
    """Kutsuu Gemini-mallia ja palauttaa validoidun AnalysisResult-objektin."""
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=build_user_prompt(data),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            response_mime_type="application/json",
            response_schema=AnalysisResult,
        ),
    )

    # google-genai palauttaa valmiiksi parsitun Pydantic-objektin .parsed-kentässä,
    # kun response_schema on annettu. Varaudutaan silti siihen, ettei sitä syystä
    # tai toisesta olisi saatavilla, ja parsitaan tällöin raaka JSON-teksti itse.
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, AnalysisResult):
        return parsed

    raw_text = response.text
    if not raw_text:
        raise ValueError("Mallilta ei saatu vastaussisältöä.")

    try:
        data_dict = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Vastausta ei voitu tulkita JSON-muodossa: {exc}") from exc

    return AnalysisResult.model_validate(data_dict)


# ---------------------------------------------------------------------------
# Tulosten esitys
# ---------------------------------------------------------------------------

SEVERITY_STYLE = {
    Severity.KRIITTINEN: {"emoji": "🔴", "color": "#E5484D", "label": "Kriittinen"},
    Severity.KOHTALAINEN: {"emoji": "🟠", "color": "#E8A33D", "label": "Kohtalainen"},
    Severity.HUOMIOITAVA: {"emoji": "🟢", "color": "#9AD13A", "label": "Huomioitava"},
}

SEVERITY_ORDER = {Severity.KRIITTINEN: 0, Severity.KOHTALAINEN: 1, Severity.HUOMIOITAVA: 2}


def render_red_flag_card(flag: RedFlag):
    style = SEVERITY_STYLE[flag.severity]
    st.markdown(
        f"""
        <div style="
            border-left: 6px solid {style['color']};
            background-color: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 6px solid {style['color']};
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
        ">
            <div style="font-weight:600; font-size:1.0rem; color:#FFFFFF;">
                {style['emoji']} {flag.title}
                <span style="
                    float:right;
                    font-size:0.75rem;
                    font-weight:700;
                    color:{style['color']};
                    border:1px solid {style['color']};
                    border-radius: 10px;
                    padding: 1px 8px;
                ">{style['label'].upper()}</span>
            </div>
            <div style="margin-top:0.35rem; font-size:0.92rem; color:#D6E0DA;">{flag.explanation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis(result: AnalysisResult):
    st.subheader("📋 Analyysin tulokset")

    # --- Yhteenveto ---
    st.info(f"**Kokonaisarvio:** {result.overall_risk_summary}")

    # --- Red flags ---
    st.markdown("### 🚩 Havaitut riskit / Red Flags")
    if not result.red_flags:
        st.write("Ei merkittäviä riskihavaintoja.")
    else:
        counts = {sev: 0 for sev in Severity}
        for flag in result.red_flags:
            counts[flag.severity] += 1

        m1, m2, m3 = st.columns(3)
        m1.metric("🔴 Kriittiset", counts[Severity.KRIITTINEN])
        m2.metric("🟠 Kohtalaiset", counts[Severity.KOHTALAINEN])
        m3.metric("🟢 Huomioitavat", counts[Severity.HUOMIOITAVA])

        st.markdown("")
        sorted_flags = sorted(result.red_flags, key=lambda f: SEVERITY_ORDER[f.severity])
        for flag in sorted_flags:
            render_red_flag_card(flag)

    # --- Kysymykset johdolle ---
    st.markdown("### ❓ Kysymykset johdolle / toimitusjohtajalle")
    if not result.questions_for_management:
        st.write("Ei erillisiä kysymyksiä.")
    else:
        for i, q in enumerate(result.questions_for_management, start=1):
            with st.expander(f"{i}. [{q.topic}] {q.question}"):
                st.markdown("**Mitä vastauksessa kannattaa tarkkailla:**")
                st.write(q.what_to_look_for)

    # --- Suositellut toimenpiteet ---
    st.markdown("### ✅ Suositellut toimenpiteet / sopimusehdot")
    if not result.recommended_actions:
        st.write("Ei erillisiä suosituksia.")
    else:
        for action in result.recommended_actions:
            st.markdown(f"- {action}")

    # --- Lataus ---
    st.divider()
    st.download_button(
        "⬇️ Lataa analyysi (.json)",
        data=result.model_dump_json(indent=2),
        file_name=f"due_diligence_{st.session_state['company_name'] or 'yritys'}.json",
        mime="application/json",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Sivupalkki
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Asetukset")

    st.text_input(
        "Google Gemini API -avain",
        type="password",
        key="manual_api_key",
        placeholder="Jätä tyhjäksi, jos avain on jo asetettu secrets/env-muuttujaan",
        help=(
            "Jos kenttä jätetään tyhjäksi, avain haetaan järjestyksessä "
            "st.secrets['GEMINI_API_KEY'] tai ympäristömuuttujasta GEMINI_API_KEY."
        ),
    )

    resolved_key = resolve_api_key(st.session_state["manual_api_key"])
    if resolved_key:
        st.success("API-avain löytyi ✅", icon="🔑")
    else:
        st.warning("API-avainta ei ole vielä asetettu.", icon="⚠️")

    st.divider()
    st.subheader("🏢 Yrityksen perustiedot")

    st.text_input("Yrityksen nimi", key="company_name")
    st.text_input("Toimiala", key="industry")
    st.selectbox("Valuatumin luottoluokka", CREDIT_RATINGS, key="credit_rating")

    st.divider()
    st.button(
        "📥 Lataa esimerkkidata",
        on_click=load_example_data,
        use_container_width=True,
        help="Täyttää lomakkeen teollisuusyrityksellä, jonka liikevaihto kasvaa mutta kassa kuivuu.",
    )


# ---------------------------------------------------------------------------
# Päänäkymä
# ---------------------------------------------------------------------------

st.subheader("Talousluvut")

col1, col2 = st.columns(2)

with col1:
    st.number_input(
        "Liikevaihto (€)",
        min_value=0.0,
        step=10_000.0,
        format="%.0f",
        key="revenue",
    )
    st.number_input(
        "Liiketulos / EBIT (%)",
        step=0.1,
        format="%.1f",
        key="ebit_margin",
    )
    st.number_input(
        "Omavaraisuusaste (%)",
        step=0.1,
        format="%.1f",
        key="equity_ratio",
    )

with col2:
    st.number_input(
        "Liikevaihdon muutos (%)",
        step=0.1,
        format="%.1f",
        key="revenue_change",
    )
    st.number_input(
        "Quick Ratio",
        step=0.01,
        format="%.2f",
        key="quick_ratio",
    )
    st.number_input(
        "Myyntisaamisten kiertoaika (päivää)",
        min_value=0.0,
        step=1.0,
        format="%.0f",
        key="dso_days",
    )

st.text_area(
    "Muut huomiot / johdon kommentit",
    key="notes",
    height=120,
    placeholder=(
        "Esim. johdon selitykset kasvulle, investoinnit, poikkeukselliset erät, "
        "asiakaskeskittymä, tulevat rahoitustarpeet..."
    ),
)

analyze_clicked = st.button(
    "🔍 Analysoi riskit ja luo neuvottelulista",
    type="primary",
    use_container_width=True,
)

st.divider()

if analyze_clicked:
    api_key = resolve_api_key(st.session_state["manual_api_key"])

    if not api_key:
        st.error(
            "API-avainta ei löytynyt. Syötä avain sivupalkkiin tai aseta "
            "GEMINI_API_KEY st.secrets- tai ympäristömuuttujaan."
        )
    elif not st.session_state["company_name"]:
        st.error("Syötä vähintään yrityksen nimi ennen analyysin käynnistämistä.")
    else:
        data = {k: st.session_state[k] for k in DEFAULT_VALUES.keys()}
        with st.spinner("Analysoidaan taloustietoja Geminin avulla..."):
            try:
                st.session_state["analysis_result"] = call_gemini(api_key, data)
            except Exception as exc:
                st.session_state["analysis_result"] = None
                st.error(f"Virhe Gemini-kutsussa tai vastauksen käsittelyssä: {exc}")

if st.session_state["analysis_result"] is not None:
    render_analysis(st.session_state["analysis_result"])


# ---------------------------------------------------------------------------
# requirements.txt (kopioi tämä osio erilliseen requirements.txt-tiedostoon,
# tai käytä tämän tiedoston vieressä olevaa valmista requirements.txt-tiedostoa)
# ---------------------------------------------------------------------------
#
# streamlit
# google-genai
# pydantic
