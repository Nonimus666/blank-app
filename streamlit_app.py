import html
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

st.set_page_config(page_title="Weekoverzicht productiviteit", layout="centered")

DATA_FILE = Path(__file__).with_name("tasks.json")
DAYS = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
MINUTE_CHOICES = [0, 15, 30, 45]

CSS = """
<style>
:root {
    --green: #2e9e5b;
    --yellow: #f2b705;
    --open: rgba(128, 128, 128, .55);
    --bw: 44px;   /* breedte van 1 uur */
    --bh: 30px;   /* hoogte van een blok */
}
@media (max-width: 640px) { :root { --bw: 26px; --bh: 24px; } }

/* ---- blokken ---- */
.day-blocks { display:flex; flex-wrap:wrap; gap:10px 3px; align-items:center; min-height:44px; }
details.grp { position:relative; }
details.grp > summary { list-style:none; cursor:pointer; display:flex; gap:3px; outline:none; }
details.grp > summary::-webkit-details-marker { display:none; }
.block { height:var(--bh); width:var(--bw); border-radius:5px; box-sizing:border-box; transition:transform .12s, filter .12s; }
.block.q25 { width:calc(var(--bw) * .25); }
.block.q50 { width:calc(var(--bw) * .5); }
.block.q75 { width:calc(var(--bw) * .75); }
.block.done { background:var(--green); }
.block.late { background:var(--yellow); }
.block.open { border:2px solid var(--open); }
.block.running { border:2px solid var(--yellow); }
details.grp > summary:hover .block { transform:translateY(-2px); filter:brightness(1.07); }
.none { opacity:.35; font-size:.9rem; }
.today { margin-right:9px; font-size:.72rem; opacity:.6; border:1px solid var(--open); border-radius:999px; padding:1px 8px; }

/* ---- pop-up boven de blokken ---- */
.tip { position:absolute; bottom:calc(100% + 10px); left:0; z-index:60; min-width:190px; max-width:260px;
       padding:10px 13px; border-radius:10px; background:#1f2937; color:#f3f4f6;
       box-shadow:0 6px 20px rgba(0,0,0,.25); font-size:.85rem; line-height:1.35; }
.tip::after { content:""; position:absolute; top:100%; left:18px; border:7px solid transparent; border-top-color:#1f2937; }
.tip b { display:block; font-size:.92rem; margin-bottom:3px; }
.tip span { display:block; opacity:.8; }
.tip .st-done { color:#6ee7a0; opacity:1; }
.tip .st-late { color:#fcd34d; opacity:1; }

/* ---- dagknoppen ---- */
[class*="st-key-day_"] button, [class*="st-key-dayopen_"] button { padding-left:4px; }
[class*="st-key-day_"] button > div, [class*="st-key-dayopen_"] button > div,
[class*="st-key-day_"] button [data-testid="stMarkdownContainer"], [class*="st-key-dayopen_"] button [data-testid="stMarkdownContainer"] {
    width:100%; justify-content:flex-start; text-align:left; }
[class*="st-key-day_"] button p, [class*="st-key-dayopen_"] button p { text-align:left; }
[class*="st-key-day_"] button p, [class*="st-key-dayopen_"] button p { font-weight:600; font-size:1.05rem; }
[class*="st-key-day_"] button p::after { content:""; display:inline-block; width:6px; height:6px; margin-left:9px;
    border-right:2px solid currentColor; border-bottom:2px solid currentColor; transform:rotate(-45deg); opacity:.4; }
[class*="st-key-dayopen_"] button p { color:var(--green); }
[class*="st-key-dayopen_"] button p::after { content:""; display:inline-block; width:6px; height:6px; margin-left:9px;
    border-right:2px solid currentColor; border-bottom:2px solid currentColor; transform:rotate(45deg) translateY(-2px); }

/* ---- uitschuivend gedeelte van een dag ---- */
[class*="st-key-panel_"] { background:rgba(128,128,128,.07); border-radius:14px; padding:14px 16px; margin:2px 0 18px 0;
    animation:slidein .25s ease-out; }
@keyframes slidein { from { opacity:0; transform:translateY(-10px); } to { opacity:1; transform:none; } }
[class*="st-key-phead_"] { border-bottom:1px solid rgba(128,128,128,.25); padding-bottom:6px; }
.tname { font-size:1rem; font-weight:500; }
.tmeta { opacity:.65; font-size:.85rem; }
.countdown { font-variant-numeric:tabular-nums; font-weight:600; }
.countdown.over { color:var(--yellow); }

/* rijen netjes naast elkaar houden, ook op een telefoon */
[class*="st-key-row_"] [data-testid="stHorizontalBlock"], [class*="st-key-panel_"] [data-testid="stHorizontalBlock"],
[class*="st-key-nav_"] [data-testid="stHorizontalBlock"] {
    flex-wrap:nowrap !important; gap:.5rem !important; }
[class*="st-key-row_"] [data-testid="stColumn"], [class*="st-key-panel_"] [data-testid="stColumn"], [class*="st-key-nav_"] [data-testid="stColumn"],
[class*="st-key-row_"] [data-testid="column"], [class*="st-key-panel_"] [data-testid="column"], [class*="st-key-nav_"] [data-testid="column"] {
    min-width:0 !important; width:auto !important; }
@media (max-width: 640px) {
    [class*="st-key-nav_"] button { padding:0 6px; }
    [class*="st-key-nav_"] button p { font-size:.8rem; }
    [class*="st-key-panel_"] button { padding:0 4px; }
    [class*="st-key-panel_"] button p { font-size:.76rem; white-space:nowrap; }
}

/* ---- wis-kruisje: grijs, ronde uiteinden, rood bij muis erop ---- */
:is([class*="st-key-del_"], [class*="st-key-close_"]) button { width:32px; min-height:32px; padding:0; border:none; background-color:transparent;
    background-repeat:no-repeat; background-position:center; background-size:16px;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239aa0a6' stroke-width='2.6' stroke-linecap='round'%3E%3Cpath d='M6 6l12 12M18 6L6 18'/%3E%3C/svg%3E");
    transition:background-color .15s; }
:is([class*="st-key-del_"], [class*="st-key-close_"]) button:hover { background-color:rgba(229,72,77,.12);
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e5484d' stroke-width='2.6' stroke-linecap='round'%3E%3Cpath d='M6 6l12 12M18 6L6 18'/%3E%3C/svg%3E"); }
:is([class*="st-key-del_"], [class*="st-key-close_"]) button p { display:none; }

.legend { display:flex; gap:20px; font-size:.85rem; opacity:.8; margin:4px 0 12px 0; flex-wrap:wrap; }
.legend span { display:inline-flex; align-items:center; gap:6px; }
.legend .block { height:12px; width:12px; border-radius:3px; }
.summary { font-size:.95rem; opacity:.85; margin:18px 0 2px 0; }
</style>
"""


def now() -> datetime:
    """Huidige tijd in Nederland (de online server draait anders op UTC)."""
    return datetime.now(ZoneInfo("Europe/Amsterdam")).replace(tzinfo=None)


# ---------- inloggen ----------
def require_password():
    """Vraagt om een wachtwoord als er een is ingesteld (online). Lokaal: geen wachtwoord."""
    try:
        password = st.secrets["app_password"]
    except (KeyError, FileNotFoundError):
        return
    if st.session_state.get("ingelogd"):
        return
    st.title("Inloggen")
    with st.form("login"):
        entered = st.text_input("Wachtwoord", type="password")
        if st.form_submit_button("Open") and entered == password:
            st.session_state.ingelogd = True
            st.rerun()
        elif entered:
            st.error("Wachtwoord klopt niet.")
    st.stop()


# ---------- opslag ----------
# Online: Supabase (database, bewaart alles blijvend).
# Lokaal zonder instellingen: een bestandje tasks.json naast de app.
def supabase_config():
    try:
        sb = st.secrets["supabase"]
        return sb["url"].rstrip("/") + "/rest/v1/tasks", {
            "apikey": sb["key"],
            "Authorization": f"Bearer {sb['key']}",
            "Content-Type": "application/json",
        }
    except (KeyError, FileNotFoundError):
        return None


def load_tasks():
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        r = requests.get(url, headers=headers, params={"select": "*"}, timeout=15)
        r.raise_for_status()
        return r.json()
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_local(tasks):
    DATA_FILE.write_text(json.dumps(tasks, indent=2))


def add_task(task):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.post(url, headers=headers, json=task, timeout=15).raise_for_status()
    else:
        _save_local(load_tasks() + [task])


def update_task(task_id, **changes):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.patch(
            url, headers=headers, params={"id": f"eq.{task_id}"}, json=changes, timeout=15
        ).raise_for_status()
    else:
        tasks = load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t.update(changes)
        _save_local(tasks)


def delete_task(task_id):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.delete(url, headers=headers, params={"id": f"eq.{task_id}"}, timeout=15).raise_for_status()
    else:
        _save_local([t for t in load_tasks() if t["id"] != task_id])


# ---------- helpers ----------
def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def new_id() -> str:
    # begint met de tijd, zodat taken altijd in de volgorde van toevoegen blijven staan
    return f"{now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6]}"


def sort_key(t):
    return ("-" in t["id"], t["id"])


def quarters(hours) -> int:
    return max(1, round(float(hours) * 4))


def fmt_duration(hours) -> str:
    minutes = quarters(hours) * 15
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} uur {m} min"
    return f"{h} uur" if h else f"{m} min"


def fmt_total(hours) -> str:
    return fmt_duration(hours) if hours else "0 min"


def status_text(task):
    if task["status"] == "done":
        return "Op tijd afgerond", "st-done"
    if task["status"] == "late":
        return "Niet op tijd afgerond", "st-late"
    if task.get("started_at"):
        return "Bezig, timer loopt", ""
    return "Nog open", ""


def group_html(task):
    """Een groep blokken (1 taak). Klik erop voor een pop-up met wat er gedaan is."""
    running = bool(task.get("started_at"))
    state = task["status"] if task["status"] != "open" else ("running" if running else "open")
    full, rest = divmod(quarters(task["hours"]), 4)
    blocks = "".join(f'<div class="block {state}"></div>' for _ in range(full))
    if rest:
        blocks += f'<div class="block q{rest * 25} {state}"></div>'
    label, css = status_text(task)
    extra = ""
    if task.get("finished_at"):
        extra = f"<span>Afgerond om {datetime.fromisoformat(task['finished_at']):%H:%M}</span>"
    tip = (
        f'<div class="tip"><b>{html.escape(task["title"])}</b>'
        f'<span>{fmt_duration(task["hours"])}</span>'
        f'<span class="{css}">{label}</span>{extra}</div>'
    )
    return f'<details class="grp" name="tip"><summary>{blocks}</summary>{tip}</details>'


def finish(task):
    """Markeer als gelukt. Als de timer liep en de deadline verstreken is -> geel."""
    status = "done"
    if task.get("started_at"):
        deadline = datetime.fromisoformat(task["started_at"]) + timedelta(hours=float(task["hours"]))
        if now() > deadline:
            status = "late"
    update_task(task["id"], status=status, finished_at=now().isoformat())


@st.fragment(run_every="1s")
def countdown(task):
    deadline = datetime.fromisoformat(task["started_at"]) + timedelta(hours=float(task["hours"]))
    left = (deadline - now()).total_seconds()
    over = left < 0
    secs = int(abs(left))
    text = f"{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}"
    label = "Tijd verstreken" if over else "Tijd over"
    st.markdown(
        f'<div class="tmeta">{label}</div><div class="countdown {"over" if over else ""}">{text}</div>',
        unsafe_allow_html=True,
    )


def duration_inputs(prefix, hours=1, minutes=0):
    c1, c2 = st.columns(2)
    h = c1.number_input("Uren", 0, 12, int(hours), 1, key=f"{prefix}_h")
    m = c2.selectbox("Minuten", MINUTE_CHOICES, index=MINUTE_CHOICES.index(minutes), key=f"{prefix}_m")
    return h + m / 60


# ---------- uitschuifbaar gedeelte van een dag ----------
def day_panel(day: date, day_tasks):
    iso = day.isoformat()
    with st.container(key=f"panel_{iso}"):
        with st.container(key=f"phead_{iso}"):
            c_head, c_close = st.columns([12, 1], vertical_alignment="center")
            c_head.markdown(
                f'<div class="tmeta">{DAYS[day.weekday()]} {day:%d-%m}</div>', unsafe_allow_html=True
            )
            if c_close.button("x", key=f"close_{iso}", help="Sluit deze dag"):
                st.session_state.open_day = None
                st.rerun()
        if not day_tasks:
            st.markdown('<div class="tmeta">Nog geen taken op deze dag.</div>', unsafe_allow_html=True)

        for t in day_tasks:
            label, _ = status_text(t)
            c_info, c_del = st.columns([12, 1], vertical_alignment="center")
            c_info.markdown(
                f'<div class="tname">{html.escape(t["title"])}</div>'
                f'<div class="tmeta">{fmt_duration(t["hours"])} &middot; {label}</div>',
                unsafe_allow_html=True,
            )
            if c_del.button("x", key=f"del_{t['id']}", help="Verwijder taak"):
                delete_task(t["id"])
                st.rerun()

            a, b, c, d = st.columns(4, vertical_alignment="center")
            if t["status"] == "open":
                if t.get("started_at"):
                    with a:
                        countdown(t)
                elif a.button("Start", key=f"start_{t['id']}", width="stretch"):
                    update_task(t["id"], started_at=now().isoformat())
                    st.rerun()
                if b.button("Gelukt", key=f"done_{t['id']}", type="primary", width="stretch"):
                    finish(t)
                    st.rerun()
                if c.button("Niet gelukt", key=f"late_{t['id']}", width="stretch"):
                    update_task(t["id"], status="late", finished_at=now().isoformat())
                    st.rerun()
            elif a.button("Heropen", key=f"reopen_{t['id']}", width="stretch"):
                update_task(t["id"], status="open", started_at=None, finished_at=None)
                st.rerun()

            with d.popover("Wijzig", width="stretch"):
                with st.form(f"edit_{t['id']}"):
                    new_title = st.text_input("Taak", t["title"], key=f"edit_title_{t['id']}")
                    mins = quarters(t["hours"]) * 15
                    snapped = min(MINUTE_CHOICES, key=lambda x: abs(x - mins % 60))
                    new_hours = duration_inputs(f"edit_{t['id']}", mins // 60, snapped)
                    if st.form_submit_button("Opslaan") and new_title.strip() and new_hours > 0:
                        update_task(t["id"], title=new_title.strip(), hours=new_hours)
                        st.rerun()
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        with st.form(f"add_{iso}", clear_on_submit=True):
            st.markdown("**Nieuwe taak**")
            title = st.text_input("Wat ga je doen?", key=f"add_title_{iso}")
            hours = duration_inputs(f"add_{iso}", 1, 0)
            if st.form_submit_button("Toevoegen", type="primary") and title.strip() and hours > 0:
                add_task(
                    {
                        "id": new_id(),
                        "date": iso,
                        "title": title.strip(),
                        "hours": hours,
                        "status": "open",
                        "started_at": None,
                        "finished_at": None,
                    }
                )
                st.rerun()


# ---------- state ----------
if "week_start" not in st.session_state:
    st.session_state.week_start = monday_of(now().date())
if "open_day" not in st.session_state:
    st.session_state.open_day = None

st.markdown(CSS, unsafe_allow_html=True)
require_password()
st.title("Weekoverzicht")

tasks = load_tasks()
week_start: date = st.session_state.week_start
week_days = [week_start + timedelta(days=i) for i in range(7)]
week_tasks = sorted(
    (t for t in tasks if date.fromisoformat(t["date"]) in week_days), key=sort_key
)

# navigatie
iso_cal = week_start.isocalendar()
with st.container(key="nav_week"):
    nav_l, nav_m, nav_r = st.columns([1.4, 2.6, 1.6], vertical_alignment="center")
    if nav_l.button("Vorige", width="stretch"):
        st.session_state.week_start = week_start - timedelta(days=7)
        st.session_state.open_day = None
        st.rerun()
    if nav_r.button("Volgende", width="stretch"):
        st.session_state.week_start = week_start + timedelta(days=7)
        st.session_state.open_day = None
        st.rerun()
    nav_m.markdown(
        f"<div style='text-align:center'>Week {iso_cal.week} &middot; "
        f"{week_days[0]:%d-%m} t/m {week_days[6]:%d-%m-%Y}</div>",
        unsafe_allow_html=True,
    )

has_weekend_tasks = any(date.fromisoformat(t["date"]).weekday() >= 5 for t in week_tasks)
show_weekend = st.checkbox("Weekend tonen (za / zo)", value=has_weekend_tasks)

st.markdown(
    '<div class="legend">'
    '<span><div class="block done"></div>Op tijd gelukt</span>'
    '<span><div class="block late"></div>Niet op tijd</span>'
    '<span><div class="block open"></div>Nog open</span>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------- dagen ----------
visible = week_days if show_weekend else week_days[:5]
for day in visible:
    iso = day.isoformat()
    day_tasks = [t for t in week_tasks if t["date"] == iso]
    is_open = st.session_state.open_day == iso

    with st.container(key=f"row_{iso}"):
        c_name, c_blocks = st.columns([2, 5], vertical_alignment="center")
        key = f"dayopen_{iso}" if is_open else f"day_{iso}"
        if c_name.button(DAYS[day.weekday()], key=key, type="tertiary", width="stretch"):
            st.session_state.open_day = None if is_open else iso
            st.rerun()
        pill = '<span class="today">vandaag</span>' if day == now().date() else ""
        groups = "".join(group_html(t) for t in day_tasks) or '<span class="none">Geen taken</span>'
        c_blocks.markdown(f'<div class="day-blocks">{pill}{groups}</div>', unsafe_allow_html=True)

    if is_open:
        day_panel(day, day_tasks)

# ---------- samenvatting ----------
shown = [t for t in week_tasks if date.fromisoformat(t["date"]) in visible]
done = [t for t in shown if t["status"] == "done"]
late = [t for t in shown if t["status"] == "late"]
open_ = [t for t in shown if t["status"] == "open"]
st.markdown(
    f'<div class="summary">Deze week: <b>{len(done)}</b> op tijd '
    f"({fmt_total(sum(float(t['hours']) for t in done))}), <b>{len(late)}</b> niet op tijd, "
    f"<b>{len(open_)}</b> open.</div>",
    unsafe_allow_html=True,
)
