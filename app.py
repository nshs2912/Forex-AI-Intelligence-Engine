"""Streamlit dashboard for the Forex AI Intelligence Engine."""
import streamlit as st
import streamlit.components.v1 as components
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from forex_ai.glossary import MAJOR_PAIRS, PRECIOUS_METALS, TRADING_GLOSSARY
from forex_ai.fundamental_info import (
    FUNDAMENTAL_INDICATORS,
    fundamental_inputs_for,
    fundamental_sources_for,
)
from forex_ai.market_data import (
    MarketDataError,
    fetch_daily_history,
    fetch_live_quote,
    quote_age_seconds,
    quote_freshness,
)
from forex_ai.ml_inference import infer_from_features, load_model
from forex_ai.feature_engineering import build_features
from forex_ai.dss_governance import assess_dss
from forex_ai.model_validation import validate_model_artifact
from forex_ai.probability import unavailable_result
from forex_ai.risk_engine import build_trade_setup
from forex_ai.risk_validation import validate_trade_risk
from forex_ai.signal_engine import combine_signals

st.set_page_config(page_title="Forex AI Market Intelligence Monitor", layout="wide")
st.title("Forex AI Market Intelligence Monitor")
st.caption("Market state + Fundamental Evidence + ML Intelligence + DSS Governance + Risk observability.")

INSTRUMENTS = list(MAJOR_PAIRS) + list(PRECIOUS_METALS)

with st.sidebar:
    st.header("Trade setup")
    data_mode = st.radio("Market data", ["Live", "Demo"], horizontal=True)
    timezone_options = {
        "WIB (UTC+7)": "Asia/Jakarta",
        "WITA (UTC+8)": "Asia/Makassar",
        "WIT (UTC+9)": "Asia/Jayapura",
    }
    display_timezone = st.selectbox("Zona waktu", list(timezone_options), index=0)
    instrument = st.selectbox("Instrument", INSTRUMENTS, index=0)
    asset_class = "Forex" if instrument in MAJOR_PAIRS else "Precious Metal"

    if data_mode == "Live":
        refresh = st.slider("Refresh interval (seconds)", 15, 300, 30, 15)
        st_autorefresh(interval=refresh * 1000, key="market_refresh")
        st.caption("Live mode requires the TWELVE_DATA_API_KEY secret.")
    else:
        refresh = 0

    side = st.selectbox("Side", ["Long", "Short"])
    entry = st.number_input("Demo Entry", min_value=0.000001, value=1.1000, format="%.6f")
    atr = st.number_input("ATR", min_value=0.000001, value=0.0080, format="%.6f")
    atr_multiplier = st.slider("ATR multiplier", 0.5, 4.0, 1.5, 0.1)
    rr = st.slider("Risk / Reward", 1.0, 5.0, 2.0, 0.1)
    balance = st.number_input("Account balance", min_value=1.0, value=10000.0)
    risk_pct = st.slider("Risk per trade (%)", 0.1, 5.0, 1.0, 0.1)

    st.divider()
    with st.expander("📖 Trading Glossary", expanded=False):
        category = st.selectbox("Category", list(TRADING_GLOSSARY))
        terms = TRADING_GLOSSARY[category]
        term = st.selectbox("Term", list(terms))
        st.markdown(f"**{term}**")
        st.write(terms[term])

pair_description = MAJOR_PAIRS.get(instrument) or PRECIOUS_METALS[instrument]
st.subheader(f"📊 {instrument}")
st.info(pair_description)

live_quote = None
if data_mode == "Live":
    try:
        live_quote = fetch_live_quote(instrument)
        entry = live_quote.price
        age_seconds = quote_age_seconds(live_quote)
        freshness = quote_freshness(age_seconds)
        live_tz = timezone_options[display_timezone]
        components.html(
            f"""
            <div style="font-family: sans-serif; padding: 10px 14px; border-radius: 8px; border: 1px solid #2e7d32;">
              <div id="live-status" style="font-size: 1rem; font-weight: 700;">
                📡 LIVE — {live_quote.source} | {live_quote.symbol} | {live_quote.price:.6f}
              </div>
              <div id="live-clock" style="font-size: 1rem; font-weight: 600; margin-top: 4px;"></div>
              <div style="font-size: 0.78rem; opacity: 0.72; margin-top: 3px;">
                Jam dashboard berjalan • {display_timezone}
              </div>
            </div>
            <script>
              const liveTz = {live_tz!r};
              function updateLiveClock() {{
                const parts = new Intl.DateTimeFormat("en-GB", {{
                  timeZone: liveTz,
                  day: "2-digit", month: "2-digit", year: "numeric",
                  hour: "2-digit", minute: "2-digit", second: "2-digit",
                  hour12: true
                }}).formatToParts(new Date());
                const get = (name) => parts.find(p => p.type === name)?.value || "";
                document.getElementById("live-clock").textContent =
                  "🕐 " + get("day") + "-" + get("month") + "-" + get("year") + " " +
                  get("hour") + ":" + get("minute") + ":" + get("second") + " " +
                  get("dayPeriod") + " {display_timezone}";
              }}
              updateLiveClock();
              setInterval(updateLiveClock, 1000);
            </script>
            """,
            height=88,
        )
        received_local = live_quote.received_at.astimezone(ZoneInfo(live_tz))
        st.caption(
            f"Quote timestamp: {live_quote.timestamp.astimezone(ZoneInfo(live_tz)):%d-%m-%Y %I:%M:%S %p} "
            f"{display_timezone} · Received: {received_local:%d-%m-%Y %I:%M:%S %p} {display_timezone} "
            f"· Age: {age_seconds:.0f}s · Status: {freshness}"
        )
        if live_quote.bid is not None and live_quote.ask is not None:
            st.caption(
                f"Bid: {live_quote.bid:.6f} · Ask: {live_quote.ask:.6f} · "
                f"Spread: {live_quote.ask - live_quote.bid:.6f}"
            )
    except MarketDataError as exc:
        st.error(f"Live market data unavailable: {exc}")
        st.warning("Switch to Demo mode or configure TWELVE_DATA_API_KEY.")

with st.expander("📋 Supported instruments", expanded=False):
    st.markdown("**7 Major Currency Pairs**")
    st.write(", ".join(MAJOR_PAIRS))
    st.markdown("**Precious Metals**")
    st.write(", ".join(PRECIOUS_METALS))

st.subheader("🛰️ Market Intelligence Monitor")
mi1, mi2, mi3, mi4 = st.columns(4)
mi1.metric("Instrument", instrument)
mi2.metric("Asset Class", asset_class)
mi3.metric("Data Mode", data_mode)
if live_quote is not None:
    mi4.metric("Quote Status", f"{freshness} · {age_seconds:.0f}s")
else:
    mi4.metric("Quote Status", "DEMO / N/A")

monitor_left, monitor_right = st.columns(2)
with monitor_left:
    st.markdown("**Market Data Health**")
    if live_quote is not None:
        st.write(f"Provider: {live_quote.source}")
        st.write(f"Provider timestamp: {live_quote.timestamp.isoformat()}")
        st.write(f"Application received: {live_quote.received_at.isoformat()}")
        if live_quote.bid is not None and live_quote.ask is not None:
            spread = live_quote.ask - live_quote.bid
            st.write(f"Bid/Ask spread: {spread:.6f}")
        if freshness == "FRESH":
            st.success("Market snapshot is fresh.")
        elif freshness == "AGING":
            st.warning("Market snapshot is aging; refresh before relying on it.")
        else:
            st.error("Market snapshot is stale.")
    else:
        st.info("No live quote. Demo mode does not represent current market conditions.")

with monitor_right:
    st.markdown("**Evidence & Feed Coverage**")
    st.write("Fundamental score: **manual input**")
    st.write("Technical score: **manual input**")
    st.write("News feed: **reference links only**")
    st.write("Economic calendar: **reference link only**")
    st.write("ML inference: **live only when completed daily features are available**")
    st.caption(
        "Coverage status is intentionally explicit so the monitor never presents "
        "reference data as an automated live fundamental/news feed."
    )


st.subheader("🧭 Signal Inputs")
st.caption(
    "Saat ini Fundamental, Technical, dan ML Direction adalah input manual untuk "
    "pengujian engine. Nilainya belum berasal dari feed otomatis."
)
with st.expander("ℹ️ Dasar perhitungan Signal Score", expanded=False):
    st.markdown(
        "**Bobot ensemble saat ini:** Fundamental 25% · Technical 25% · "
        "ML Direction 30% · Market Regime 10% · Risk Filter 10%."
    )
    st.markdown(
        "**Skala setiap komponen:** −1 = bearish kuat · 0 = netral · "
        "+1 = bullish kuat. Score akhir adalah gabungan berbobot, bukan probabilitas."
    )
    st.markdown(
        "**Keputusan arah:** score > +0.15 = bullish/BUY · score < −0.15 = "
        "bearish/SELL · lainnya = neutral/WAIT."
    )
    st.warning(
        "Market Regime dan Risk Filter saat ini memakai nilai default netral "
        "di engine. Fundamental dan Technical juga belum mengambil data live."
    )
c1, c2, c3 = st.columns(3)
with c1:
    fundamental = st.slider("Fundamental", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")
with c2:
    technical = st.slider("Technical", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")
with c3:
    ml = st.slider("ML Direction", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")

st.subheader("🤖 ML Model Intelligence")
with st.expander(f"Trained model status — {instrument}", expanded=False):
    try:
        model_payload = load_model(instrument)
        metrics = model_payload.get("metrics", {})
        st.success(
            f"Model artifact tersedia · {model_payload.get('model_type', 'unknown')} · "
            f"Calibration: {model_payload.get('calibration', 'unknown')}"
        )
        x1, x2, x3, x4 = st.columns(4)
        x1.metric("Model Timeframe", model_payload.get("timeframe", "N/A"))
        x2.metric("Train Rows", f"{metrics.get('train_rows', 0):,}")
        x3.metric("Test Rows", f"{metrics.get('test_rows', 0):,}")
        x4.metric("ROC-AUC", f"{metrics.get('roc_auc', 0):.3f}")
        st.caption(
            f"Training period: {metrics.get('dataset_start', 'N/A')} → "
            f"{metrics.get('dataset_end', 'N/A')} · "
            f"Model status: {model_payload.get('status', 'unknown')}"
        )
        try:
            validation = validate_model_artifact(
                f"models/{instrument.replace('/', '')}/model.json"
            )
            if validation.passed:
                st.success("Automated live-readiness gates: PASS")
            else:
                st.warning(
                    "Automated live-readiness gates: BLOCKED — "
                    + ", ".join(validation.reasons)
                )
        except (FileNotFoundError, ValueError, KeyError, OSError) as exc:
            st.warning(f"Automated live-readiness unavailable: {exc}")
        st.caption(
            "Feature model: " + ", ".join(model_payload.get("features", []))
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        st.warning(f"Model artifact belum tersedia untuk {instrument}: {exc}")

st.subheader("📚 Fundamental Intelligence")
fundamental_info = fundamental_inputs_for(instrument)
with st.expander(f"Fundamental data & drivers — {instrument}", expanded=False):
    st.info(
        "Status: reference-only. Dashboard belum menerima nilai fundamental live; "
        "jangan menganggap daftar indikator di bawah sebagai kondisi pasar saat ini."
    )
    st.markdown(f"**Driver utama {instrument}:** {fundamental_info['drivers']}")
    for indicator, details in FUNDAMENTAL_INDICATORS.items():
        st.markdown(f"**{indicator}**")
        st.write(details["description"])
        st.caption(f"Dampak yang dipantau: {details['impact']}")
        st.caption(f"Status sumber: {details['source_status']}")

    st.markdown("### 🔗 Fundamental Evidence Sources")
    st.caption(
        "Link berikut adalah sumber riset yang dapat dibuka langsung. "
        "Dashboard belum mengklaim bahwa berita tersebut adalah feed live atau otomatis telah memengaruhi score."
    )
    for source in fundamental_sources_for(instrument):
        label = f"{source['source_type'].upper()} · {source['currency']} · {source['description']}"
        st.markdown(f"- **{source['evidence_id']}** — [{label}]({source['url']})")

    st.info(
        "Untuk berita terbaru, gunakan sumber berita yang tercantum dan verifikasi "
        "waktu publikasi, relevansi terhadap instrument, serta sumber primer sebelum "
        "memasukkannya sebagai evidence fundamental."
    )

# Start without a probability; live ML inference replaces this only when all
# required daily features and a governed model artifact are available.
probability = unavailable_result()
ml_inference = None
ml_data_status = "not_attempted"
if data_mode == "Live" and instrument in MAJOR_PAIRS and live_quote is not None:
    try:
        history = fetch_daily_history(instrument, outputsize=60)
        today_utc = live_quote.received_at.date()
        history = history[history["date"].dt.date < today_utc].copy()
        feature_frame = build_features(history)
        if feature_frame.empty:
            raise ValueError("insufficient completed daily bars for ML features")
        latest = feature_frame.iloc[-1]
        live_model_payload = load_model(instrument)
        feature_names = live_model_payload.get("features", [])
        if not feature_names:
            raise ValueError("model feature contract is empty")
        features = {name: float(latest[name]) for name in feature_names}
        ml_inference = infer_from_features(instrument, features)
        probability = ml_inference.probability
        ml = 2.0 * float(probability.bullish_probability) - 1.0
        ml_data_status = "live_inference"
    except (MarketDataError, FileNotFoundError, ValueError, KeyError) as exc:
        ml_data_status = f"unavailable: {exc}"

signal = combine_signals(fundamental, technical, ml)

if signal.direction == "bullish":
    raw_action = "BUY"
elif signal.direction == "bearish":
    raw_action = "SELL"
else:
    raw_action = "WAIT"

risk_side = (
    "Long" if raw_action == "BUY"
    else "Short" if raw_action == "SELL"
    else side
)

setup = build_trade_setup(
    risk_side,
    entry,
    atr,
    atr_multiplier=atr_multiplier,
    rr=rr,
    account_balance=balance,
    risk_pct=risk_pct,
)

try:
    artifact_path = f"models/{instrument.replace("/", "")}/model.json"
    validation_result = validate_model_artifact(artifact_path)
    validation_passed = validation_result.passed
except (FileNotFoundError, ValueError, KeyError, OSError):
    validation_result = None
    validation_passed = False

risk_controls_ok = validate_trade_risk(
    risk_distance=setup.risk_distance,
    reward_distance=setup.reward_distance,
    risk_reward=setup.risk_reward,
    position_units=setup.position_units,
    risk_pct=risk_pct,
)

dss = assess_dss(
    model_status=(
        ml_inference.model.status
        if ml_inference is not None
        else "model_unavailable"
    ),
    calibrated=probability.calibrated,
    data_fresh=(live_quote is not None) if data_mode == "Live" else False,
    feature_parity=ml_inference is not None,
    model_metrics_available=bool(
        ml_inference is not None and ml_inference.model.metrics
    ),
    risk_controls_ok=risk_controls_ok,
    validation_passed=validation_passed,
    paper_evidence_passed=False,
    approval_record_valid=False,
)

trade_action = raw_action if dss.ready else "GOVERNED"

st.subheader("🎯 AI Market Signal")
a0, a1, a2, a3 = st.columns(4)
a0.metric("DSS Action", trade_action)
a1.metric("Reference Price", f"{entry:.6f}")
a2.metric(
    "Bullish",
    f"{probability.bullish_probability:.1%}" if probability.bullish_probability is not None else "N/A",
)
a3.metric(
    "Bearish",
    f"{probability.bearish_probability:.1%}" if probability.bearish_probability is not None else "N/A",
)
st.caption(
    "Probability hanya ditampilkan bila calibrated inference benar-benar tersedia. "
    "Signal Score bukan probabilitas."
)

m0, m1, m2, m3, m4 = st.columns(5)
m0.metric("Asset Class", asset_class)
m1.metric("Direction", signal.direction.title())
m2.metric("Stop Loss", f"{setup.stop_loss:.6f}")
m3.metric("Take Profit", f"{setup.take_profit:.6f}")
m4.metric("R:R", f"{setup.risk_reward:.2f}")
st.caption(
    f"Signal confidence: {signal.confidence:.0%} · "
    f"Raw direction: {raw_action} · Probability status: {probability.status} · ML data: {ml_data_status}"
)

st.subheader("🧭 DSS Governance")
if dss.ready:
    st.success("DSS STATUS: READY")
else:
    st.warning("DSS STATUS: GOVERNED / NOT LIVE")
st.caption(
    "Output DSS bersifat decision-support dan harus dapat ditelusuri ke data, "
    "feature, model, validasi, dan risk controls."
)
with st.expander("Audit readiness details", expanded=False):
    for reason in dss.reasons:
        st.write(f"• {reason}")
    if validation_result is not None:
        st.caption(
            "Automated validation: "
            + ("PASS" if validation_result.passed else "BLOCKED")
            + " · "
            + (", ".join(validation_result.reasons) or "all checks passed")
        )
    st.caption(
        "Live approval requires a separate auditable approval record; "
        "CI/training cannot silently promote a model."
    )

st.subheader("📡 Intelligence Control Room")
ic1, ic2, ic3, ic4 = st.columns(4)
ic1.metric("Raw Direction", raw_action)
ic2.metric("DSS Action", trade_action)
ic3.metric("ML Status", ml_data_status.replace("_", " ").upper())
ic4.metric("DSS Status", dss.status)

with st.expander("🔎 Intelligence health & governance", expanded=False):
    h1, h2 = st.columns(2)
    with h1:
        st.markdown("**Data & Model Health**")
        st.write(
            "Market data: "
            + ("AVAILABLE" if live_quote is not None else "UNAVAILABLE / DEMO")
        )
        st.write(f"Quote freshness: {freshness if live_quote is not None else 'N/A'}")
        st.write(f"Feature parity: {'PASS' if ml_inference is not None else 'NOT VERIFIED'}")
        st.write(
            "Calibrated inference: "
            + ("AVAILABLE" if probability.calibrated else "UNAVAILABLE")
        )
    with h2:
        st.markdown("**Governance Gates**")
        st.write(f"Validation: {'PASS' if validation_passed else 'BLOCKED'}")
        st.write(f"Risk controls: {'PASS' if risk_controls_ok else 'BLOCKED'}")
        st.write("Paper evidence: BLOCKED / NOT REVIEWED")
        st.write("Human live approval: NOT PRESENT")
        st.caption(
            "The monitor intentionally keeps BUY/SELL behind the DSS governance "
            "gate when production evidence is incomplete."
        )

st.subheader("🛡️ Risk Plan")
st.caption("Trade Decision Card — entry dan level risiko dihitung dari harga referensi dan parameter Risk Engine.")

signal_class = {
    "BUY": "🟢 BUY",
    "SELL": "🔴 SELL",
    "WAIT": "🟡 WAIT",
    "GOVERNED": "🛡️ GOVERNED",
}[trade_action]

score = signal.score
if score > 0.60:
    score_description = "Bullish kuat"
elif score > 0.15:
    score_description = "Bullish"
elif score < -0.60:
    score_description = "Bearish kuat"
elif score < -0.15:
    score_description = "Bearish"
else:
    score_description = "Netral"

card = st.container(border=True)
with card:
    st.markdown(f"### {signal_class} · {instrument}")
    st.caption(
        f"Asset class: {asset_class} · Data mode: {data_mode}"
    )

    p0, p1, p2, p3, p4 = st.columns(5)
    p0.metric("Signal Score", f"{score:+.2f}")
    p0.caption(score_description)
    p1.metric("Entry Price", f"{setup.entry:.6f}")
    p2.metric("Stop Loss", f"{setup.stop_loss:.6f}")
    p3.metric("Take Profit", f"{setup.take_profit:.6f}")
    p4.metric("Risk / Reward", f"1 : {setup.risk_reward:.2f}")

    p5, p6, p7 = st.columns(3)
    p5.metric("Reference Price", f"{entry:.6f}")
    p6.metric("Position Units", f"{setup.position_units:,.2f}")
    p7.metric("Risk per Trade", f"{risk_pct:.1f}%")

    st.caption("Interpretasi score: −1.00 = bearish kuat · −0.15 = batas bearish · 0.00 = netral · +0.15 = batas bullish · +1.00 = bullish kuat.")

    if trade_action == "GOVERNED":
        st.warning(
            f"DSS GOVERNED — raw analysis = {raw_action}, tetapi action BUY/SELL "
            "ditahan karena seluruh production gates belum terpenuhi. Risk levels ditampilkan sebagai simulasi."
        )
    elif trade_action == "WAIT":
        st.warning("WAIT — score berada di zona netral (−0.15 sampai +0.15), sehingga belum ada arah BUY/SELL yang cukup kuat. Risk levels ditampilkan sebagai simulasi.")
    else:
        st.info(f"{trade_action} — Entry Price menggunakan harga referensi saat ini: {setup.entry:.6f}.")

st.caption(
    "Catatan: Entry Price adalah reference/live quote, bukan harga eksekusi broker. "
    "SL/TP adalah hasil kalkulasi Risk Engine berdasarkan ATR dan R:R."
)

if data_mode == "Live" and live_quote:
    tz_name = timezone_options[display_timezone]

st.divider()
st.caption(
    "⚠️ **Disclaimer:** Forex AI Intelligence Engine merupakan perangkat lunak "
    "untuk riset, analisis, simulasi, dan decision-support. Informasi, score, "
    "signal, Risk Plan, SL/TP, dan output ML bukan merupakan nasihat keuangan, "
    "rekomendasi investasi, atau jaminan keuntungan. Harga live merupakan snapshot "
    "data pasar dan bukan harga eksekusi broker. Pengguna bertanggung jawab atas "
    "keputusan dan risiko yang timbul dari penggunaannya."
)
st.caption(
    "© 2026 **NSHS Purworejo** — Forex AI Intelligence Engine. "
    "Dikembangkan untuk penelitian dan pengembangan teknologi AI, data intelligence, "
    "dan decision-support."
)
