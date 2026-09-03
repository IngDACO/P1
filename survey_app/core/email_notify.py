"""
Notificación por correo cada vez que se ejecuta un cálculo en la app.
Envía resumen técnico a diegoaco93@gmail.com via Gmail SMTP.
"""
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.application import MIMEApplication

import streamlit as st
from core import clock


def _secrets():
    return (
        st.secrets.get("GMAIL_USER",     ""),
        st.secrets.get("GMAIL_APP_PASS", ""),
        st.secrets.get("NOTIFY_TO",      ""),
    )


def _matrix_html(df) -> str:
    """Convierte el DataFrame de la matriz survey en tabla HTML para el correo."""
    if df is None:
        return ""
    try:
        cols = list(df.columns)
        header = "".join(
            f'<th style="background:#1a3a5c;color:white;padding:5px 10px">{c}</th>'
            for c in ["#"] + cols
        )
        rows_html = ""
        for i, (_, row) in enumerate(df.iterrows()):
            bg = "#f8f9fa" if i % 2 == 0 else "#ffffff"
            cells = f'<td style="padding:4px 10px;background:{bg};text-align:center">{i+1}</td>'
            cells += "".join(
                f'<td style="padding:4px 10px;background:{bg};text-align:center">{row[c]:.1f}</td>'
                for c in cols
            )
            rows_html += f"<tr>{cells}</tr>"
        return f"""
        <h3 style="color:#1a3a5c;margin-top:20px">Matriz SURVEY ingresada (mm)</h3>
        <table style="border-collapse:collapse;font-size:13px;width:100%">
          <tr>{header}</tr>
          {rows_html}
        </table>"""
    except Exception:
        return ""


def send_usage_notification(
    proyecto:    str,
    ingeniero:   str,
    all_params:  dict,
    analysis:    dict,
    opt_result:  dict,
    bs_result:   dict,
    survey_df   = None,   # pandas DataFrame con la matriz survey
    pdf_bytes:  bytes = None,
    pdf_name:   str   = None,
    admin_report: bytes = None,   # informe admin (PDF) completo
) -> bool:
    """
    Envía correo de seguimiento con resumen del cálculo.
    Retorna True si se envió OK, False si hubo error.
    """
    gmail_user, gmail_pass, notify_to = _secrets()
    if not gmail_user or not gmail_pass or not notify_to:
        return False

    best = opt_result.get("best") if opt_result else None
    ts   = clock.now().strftime("%d/%m/%Y  %H:%M")

    # ── Construir cuerpo HTML ─────────────────────────────
    def row(label, value, highlight=False):
        bg = "#fff3cd" if highlight else "#f8f9fa"
        return (f'<tr><td style="padding:5px 10px;background:{bg};'
                f'font-weight:bold;width:45%">{label}</td>'
                f'<td style="padding:5px 10px;background:{bg}">{value}</td></tr>')

    sol_html = ""
    if best:
        fb_ap  = best.get("fb_applied", best["fb"])
        extra  = abs(fb_ap - best["fb"]) > 0.01
        fb_str = f"{fb_ap:.1f} mm" + (" ⚠️ (with extra push for the wall)" if extra else "")
        sol_html = f"""
        <h3 style="color:#1a3a5c;margin-top:20px">Optimal solution</h3>
        <table style="border-collapse:collapse;width:100%;font-size:14px">
          {row("RL (lateral shift)", f"{best['rl']:+.1f} mm", True)}
          {row("FB (front shift)", fb_str, True)}
          {row("Values out of limit",     str(best['total_off']), best['total_off'] > 0)}
          {row("OFF per column",             str(best.get('off_by_col', {})))}
        </table>"""
    else:
        sol_html = "<p style='color:red'>No valid solution was found.</p>"

    bs_html = ""
    if bs_result:
        if not bs_result.get("needed"):
            bs_html = row("BSR vs BS", "BSR ≥ BS — No adjustment required ✅")
        elif bs_result.get("step"):
            bs_html = row("BSR vs BS",
                f"Paso: {bs_result['step']} mm — Zona: {bs_result.get('range_name')} ⚠️", True)
        else:
            bs_html = row("BSR vs BS",
                f"DIF = {bs_result.get('dif_original')} mm — Not found in any range ❌", True)

    p = all_params
    html = f"""
    <html><body style="font-family:'Segoe UI',Arial,sans-serif;color:#212529;max-width:680px;margin:0 auto">

    <div style="background:linear-gradient(135deg,#1a3a5c,#2e6da4);padding:20px 28px;border-radius:8px">
        <div style="color:white;font-size:26px;font-weight:900;letter-spacing:0.15em">COPEX</div>
        <div style="color:#b0c8e8;font-size:14px">Elevator Survey Analyzer — Notificación de uso</div>
    </div>

    <div style="background:#e8f4f8;padding:10px 20px;border-left:4px solid #2e6da4;margin:16px 0">
        <strong>Date:</strong> {ts}<br>
        <strong>Project:</strong> {proyecto or '(not specified)'}<br>
        <strong>Head installer/s:</strong> {ingeniero or '(not specified)'}
    </div>

    <h3 style="color:#1a3a5c">Main parameters</h3>
    <table style="border-collapse:collapse;width:100%;font-size:14px">
      {row("BS (drawing)",        f"{p.get('BS', '—')} mm")}
      {row("BSR (on site)",        f"{p.get('BSR', '—')} mm")}
      {row("BKS",              f"{p.get('BKS', '—')} mm")}
      {row("BT",               f"{p.get('BT', '—')} mm")}
      {row("RAIL",             f"{p.get('RAIL', '—')} mm")}
      {row("FRAME",            f"{p.get('FRAME', '—')} mm")}
      {row("SF1 / SF2",        f"{p.get('SF1', '—')} / {p.get('SF2', '—')} mm")}
      {row("TS",               f"{p.get('TS', '—')} mm")}
      {row("TKSW / TSW / FS",  f"{p.get('TKSW', '—')} / {p.get('TSW', '—')} / {p.get('FS', '—')} mm")}
      {row("Stops (NS)",     str(p.get('NS', '—')))}
      {row("Limiting wall",  f"{'Yes — Stop ' + str(p.get('WALL_STOP')) + ' side ' + str(p.get('WALL_SIDE')) if p.get('WALL_LIMITING') else 'No'}")}
      {row("Ctrl in frame",    f"{'Yes — side ' + str(p.get('CTRL_SIDE')) if p.get('CTRL_IN_FRAME') else 'No'}")}
    </table>

    <h3 style="color:#1a3a5c;margin-top:20px">Initial survey state</h3>
    <table style="border-collapse:collapse;width:100%;font-size:14px">
      {''.join(row(col, f"OFF: {analysis.get(col+'_OFF_COUNT',0)}  |  DIF: {round(analysis.get('DIF_'+col,0),1)} mm",
               analysis.get(col+'_OFF_COUNT',0) > 0)
               for col in ['WR','WL','FR','FL','OR','OL'])}
      {row("MAX OFF RL", f"{round(analysis.get('MAX_OFF_RL',0),1)} mm", analysis.get('MAX_OFF_RL',0) > 0)}
      {row("MAX OFF FB", f"{round(analysis.get('MAX_OFF_FB',0),1)} mm", analysis.get('MAX_OFF_FB',0) > 0)}
    </table>

    {sol_html}

    <h3 style="color:#1a3a5c;margin-top:20px">BSR vs BS analysis</h3>
    <table style="border-collapse:collapse;width:100%;font-size:14px">
      {bs_html}
    </table>

    {_matrix_html(survey_df)}

    <div style="margin-top:24px;padding:10px 16px;background:#f0f7ff;
                border-radius:6px;font-size:12px;color:#666">
        Notificación automática generada por COPEX Survey Analyzer.<br>
        {"Attachments: drawing PDF + " if pdf_bytes else ""}Survey matrix included above.
    </div>
    </body></html>
    """

    # ── Enviar via Gmail SMTP ─────────────────────────────
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"COPEX Survey — {proyecto or 'No project'} | {ts}"
        msg["From"]    = gmail_user
        msg["To"]      = notify_to

        # Cuerpo HTML
        msg.attach(MIMEText(html, "html", "utf-8"))

        # Adjunto: informe ADMIN completo (PDF)
        if admin_report:
            adm = MIMEApplication(admin_report, _subtype="pdf")
            adm.add_header("Content-Disposition", "attachment",
                           filename=f"informe_admin_{(proyecto or 'proyecto').replace(' ', '_')}.pdf")
            msg.attach(adm)

        # Adjunto: plano PDF del usuario
        if pdf_bytes:
            pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition", "attachment",
                filename=pdf_name or "plano.pdf"
            )
            msg.attach(pdf_part)

        # Adjunto: matriz survey como CSV
        if survey_df is not None:
            try:
                csv_bytes = survey_df.to_csv(index_label="Nivel").encode("utf-8")
                csv_part  = MIMEApplication(csv_bytes, _subtype="octet-stream")
                csv_part.add_header(
                    "Content-Disposition", "attachment",
                    filename="matriz_survey.csv"
                )
                msg.attach(csv_part)
            except Exception:
                pass

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, notify_to, msg.as_bytes())
        return True

    except Exception:
        traceback.print_exc()
        return False
