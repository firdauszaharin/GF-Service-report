import streamlit as st
from fpdf import FPDF
import os
import json
import tempfile
import base64
from datetime import datetime, timedelta, timezone
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# =========================================================
# 1. PENGURUSAN TEMPLATE
# =========================================================
TEMPLATE_FILE = 'templates.json'
TAMBAHAN_FILE = 'templates_tambahan.json'

def load_templates():
    defaults = {
        "SERVICE REPORT DOCUMENT": {
            "type": "document",
            "content": [
                {
                    "heading": "1. TUJUAN",
                    "paragraphs": [
                        "Pemeriksaan dilaksanakan bagi mengesahkan kewujudan dan keadaan signal output radar TERMA SCANTER 5202 yang diperlukan untuk integrasi dengan Saab R5 RIC dan seterusnya FOX Radar Extractor.",
                        "Interface yang dikenal pasti bagi tujuan integrasi ialah:"
                    ],
                    "bullets": [
                        "Analogue Video",
                        "Trigger",
                        "ACP",
                        "ARP"
                    ],
                    "paragraphs_after": [
                        "Keperluan interface tersebut adalah selaras dengan perbincangan teknikal integrasi yang menetapkan Video, Trigger, ACP dan ARP sebagai signal input kepada Saab R5 RIC."
                    ]
                },
                {
                    "heading": "2. KAEDAH PEMERIKSAAN",
                    "paragraphs": [
                        "Pemeriksaan dilaksanakan melalui pemeriksaan fizikal dan pengukuran signal menggunakan oscilloscope.",
                        "Kaedah pemeriksaan meliputi:"
                    ],
                    "numbered": [
                        "Pemeriksaan interface/connector.",
                        "Sambungan oscilloscope kepada output yang berkaitan.",
                        "Pemerhatian waveform.",
                        "Pengukuran parameter signal seperti voltage, frequency dan period.",
                        "Perbandingan bacaan dengan spesifikasi teknikal yang berkaitan."
                    ]
                },
                {
                    "heading": "3. HASIL PEMERIKSAAN",
                    "paragraphs": [
                        "Hasil pemeriksaan direkodkan berdasarkan signal dan interface yang telah diuji di lokasi."
                    ]
                },
                {
                    "heading": "4. KESIMPULAN",
                    "paragraphs": [
                        "Hasil pemeriksaan mendapati signal yang berkaitan telah dikenal pasti dan pengesahan lanjut akan dilaksanakan bagi interface yang memerlukan verification tambahan."
                    ]
                }
            ]
        },
        "INSTALLATION REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1. Pre-Installation", ["Site readiness", "Tools available", "Specs reviewed", "Materials verified", "Safety briefing"]],
                ["2. Installation", ["Equipment installed", "Cabling completed", "Power connected", "Network connected", "Grounding completed"]],
                ["3. Testing", ["System configured", "Software installed", "Functional testing", "Operating normally"]]
            ]
        },
        "KEROSAKAN TEMPLATE": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1. Inspection", ["Visual inspection", "Physical check", "Power Status"]],
                ["2. Analysis", ["Root Cause (Hardware/Network)", "External Factors"]],
                ["3. Action Taken", ["Repair / Replacement", "Configuration / Restoration", "System Testing"]]
            ]
        }
    }

    if not os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(defaults, f, indent=4, ensure_ascii=False)

    if os.path.exists(TAMBAHAN_FILE):
        try:
            with open(TAMBAHAN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return defaults

if 'all_templates' not in st.session_state:
    st.session_state['all_templates'] = load_templates()

def save_templates_to_file():
    with open(TAMBAHAN_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state['all_templates'], f, indent=4, ensure_ascii=False)

# =========================================================
# 2. DATABASE S/N
# =========================================================
sn_database = {
    "1.2 Check SN :": ["4CE442B8B8", "4CE442B8B7", "4CE442B8BD", "4CE442B8BB", "4CE442B8BC", "4CE442B8B9"],
    "3.2 Check ID :": ["1563220541", "75770141", "689509092", "1151380960", "2048014076", "338176953"],
    "4.2 Monitor 1 Check SN :": ["CNC4431M34", "CNC4431M33", "CNC4431M32", "CNC4431M39", "CNC4431M36", "CNC4431M38"],
    "4.3 Monitor 2 Check SN :": ["CNC4431M34", "CNC4431M33", "CNC4431M32", "CNC4431M39", "CNC4431M36", "CNC4431M38"],
    "5.2 Check SN :": ["UI01245140306", "UI01245140305", "UI01245140309"],
    "7.2 Check SN :": ["VHF-A-9921", "VHF-A-9922"],
    "8.2 Check SN :": ["VHF-B-8831", "VHF-B-8832"],
    "13.3 Check SN:": ["AW121390192", "AW122210344", "AW119430008"]
}

# =========================================================
# 3. PROSES IMEJ & PDF HELPER
# =========================================================
def clean_text(text):
    """Membersihkan aksara bukan Latin-1 supaya FPDF tidak crash."""
    if text is None:
        return ""
    s = str(text)
    replacements = {
        '’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-',
        '…': '...', '•': '*', '\xa0': ' '
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode('latin-1', 'replace').decode('latin-1')

def process_image(img_input, target_size=(800, 600)):
    if img_input is None:
        return None
    try:
        if hasattr(img_input, "seek"):
            img_input.seek(0)
        img = Image.open(img_input).convert("RGBA")
        background = Image.new("RGB", target_size, (255, 255, 255))
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        background.paste(img, offset, mask=img.split()[3] if img.mode == 'RGBA' else None)
        return background
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def process_signature(canvas_data):
    if canvas_data is None:
        return None
    try:
        if not hasattr(canvas_data, "shape") or not np.any(canvas_data):
            return None
        img = Image.fromarray(canvas_data.astype('uint8'))
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
        if bbox:
            img = img.crop(bbox)

        new_img = Image.new("RGB", img.size, (255, 255, 255))
        new_img.paste(img, mask=img.split()[-1])
        return new_img
    except Exception:
        return None

def pdf_split_lines(pdf_obj, width, text):
    text = clean_text(text)
    try:
        lines = pdf_obj.multi_cell(width, 5, text, split_only=True)
        return lines if lines else [""]
    except Exception:
        if not text.strip():
            return [""]
        approx_chars = max(1, int(width * 1.8))
        wrapped = []
        current = ""
        for word in text.split():
            test = f"{current} {word}".strip()
            if len(test) <= approx_chars:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = word
        if current:
            wrapped.append(current)
        return wrapped if wrapped else [""]

def get_pdf_bytes(pdf_obj):
    """Mendapatkan bytes daripada FPDF secara selamat bagi semua versi library."""
    try:
        out = pdf_obj.output(dest='S')
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        elif isinstance(out, str):
            return out.encode('latin-1', 'replace')
    except Exception:
        pass
    try:
        out = pdf_obj.output()
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        elif isinstance(out, str):
            return out.encode('latin-1', 'replace')
    except Exception:
        pass
    return b""

class VTMS_Full_Report(FPDF):
    def __init__(self, header_title=""):
        super().__init__()
        self.header_title = clean_text(header_title)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.set_text_color(100)
            self.cell(0, 5, self.header_title, 0, 1, 'R')
            self.line(10, 15, 200, 15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def cover_page(self, data, logo_path=None):
        self.add_page()
        self.rect(5, 5, 200, 287)
        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, x=75, y=20, w=60)
        self.set_font('Arial', 'B', 12)
        self.ln(65)
        self.cell(0, 5, "SYSTEM OWNER", 0, 1, 'C')
        self.set_font('Arial', 'B', 16)
        self.multi_cell(0, 8, clean_text(data['owner']).upper(), 0, 'C')
        self.ln(10)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "PROJECT REFERENCE NO:", 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, clean_text(data['ref']), 0, 'C')
        self.ln(25)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, "DOCUMENT TITLE:", 0, 1, 'C')
        self.set_font('Arial', 'B', 22)
        self.multi_cell(0, 12, clean_text(data['title']).upper(), 0, 'C')
        self.ln(35)
        for k, v in [("LOCATION", data['loc']), ("DOCUMENT ID", data['id']), ("DATE", data['dt'])]:
            self.set_x(35)
            self.set_font('Arial', 'B', 11)
            self.cell(50, 12, k, 1, 0, 'L')
            self.set_font('Arial', '', 11)
            self.cell(90, 12, clean_text(v), 1, 1, 'L')

# =========================================================
# 4. INTERFACE STREAMLIT
# =========================================================
st.set_page_config(page_title="VTMS Reporting System", layout="wide")

with st.sidebar:
    FIXED_LOGO_PATH = "logo.png"

    if os.path.exists(FIXED_LOGO_PATH):
        st.image(FIXED_LOGO_PATH, caption="Current Company Logo", width=150)
    else:
        st.warning(f"Fail {FIXED_LOGO_PATH} tidak dijumpai. Laporan dihasilkan tanpa logo.")

    with st.expander("✨ CREATE NEW TEMPLATE"):
        n_name = st.text_input("Template Name")
        n_type = st.radio("Format", ["checkbox", "technical", "document"])
        if st.button("Build Template"):
            if n_name:
                if n_type == "document":
                    st.session_state['all_templates'][n_name] = {
                        "type": "document",
                        "content": [
                            {
                                "heading": "1. TUJUAN",
                                "paragraphs": ["Tajuk atau perenggan pengenalan."],
                                "bullets": ["Item 1", "Item 2"]
                            }
                        ]
                    }
                else:
                    h_l = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"] if n_type == "checkbox" else ["NO", "ITEM", "SPEC", "ACTUAL", "RESULT"]
                    w_l = [10, 110, 15, 15, 40] if n_type == "checkbox" else [10, 75, 40, 40, 25]
                    st.session_state['all_templates'][n_name] = {"headers": h_l, "widths": w_l, "type": n_type, "content": [["1.0 DETAILS", ["First Item"]]]}
                save_templates_to_file()
                st.rerun()

    st.divider()
    selected_template = st.selectbox("Template Type:", list(st.session_state['all_templates'].keys()))
    config = st.session_state['all_templates'][selected_template]

    if config.get("type") != "document":
        with st.expander("📝 EDIT SECTION / TASKS"):
            st.subheader("Manage Sections")
            new_sec = st.text_input("New Section Name")
            col1, col2 = st.columns(2)
            if col1.button("➕ Add Section"):
                if new_sec:
                    st.session_state['all_templates'][selected_template]["content"].append([new_sec, ["New Item"]])
                    save_templates_to_file()
                    st.rerun()

            sec_names = [s[0] for s in st.session_state['all_templates'][selected_template]["content"] if isinstance(s, (list, tuple))]
            target_sec_del = st.selectbox("Select Section to Delete", sec_names if sec_names else [""])
            if col2.button("🗑️ Delete Section", type="secondary"):
                if target_sec_del:
                    st.session_state['all_templates'][selected_template]["content"] = [s for s in st.session_state['all_templates'][selected_template]["content"] if s[0] != target_sec_del]
                    save_templates_to_file()
                    st.rerun()

            st.divider()
            st.subheader("Manage Tasks")
            target_sec = st.selectbox("Select Target Section", sec_names if sec_names else [""])

            current_tasks = []
            for s in st.session_state['all_templates'][selected_template]["content"]:
                if isinstance(s, (list, tuple)) and s[0] == target_sec:
                    current_tasks = s[1]
                    break

            new_t_name = st.text_input("New Task Name")
            col3, col4 = st.columns(2)
            if col3.button("➕ Add Task"):
                if new_t_name and target_sec:
                    for item in st.session_state['all_templates'][selected_template]["content"]:
                        if isinstance(item, (list, tuple)) and item[0] == target_sec:
                            item[1].append(new_t_name)
                            break
                    save_templates_to_file()
                    st.rerun()

            target_task_del = st.selectbox("Select Task to Delete", current_tasks if current_tasks else [""])
            if col4.button("🗑️ Delete Task"):
                if target_task_del and target_sec:
                    for item in st.session_state['all_templates'][selected_template]["content"]:
                        if isinstance(item, (list, tuple)) and item[0] == target_sec:
                            if target_task_del in item[1]:
                                item[1].remove(target_task_del)
                                break
                    save_templates_to_file()
                    st.rerun()

    if st.sidebar.button("♻️ Reset to Original Template", type="secondary"):
        if os.path.exists(TAMBAHAN_FILE):
            os.remove(TAMBAHAN_FILE)
        del st.session_state['all_templates']
        st.rerun()

    st.divider()
    sys_owner = st.text_area("System Owner", "LEMBAGA PELABUHAN JOHOR")
    proj_ref = st.text_area("Project Reference", "JPA/IP/PA(S)01-222\n'VESSEL TRAFFIC MANAGEMENT SYSTEM (VTMS)'")
    header_txt = st.text_input("Header Title", "VTMS REPORT - JPA/IP/PA(S)01-222")
    doc_id = st.text_input("Document ID", "LPJPTP/VTMS/2026")
    loc = st.text_input("Location", "VTS TOWER, TANJUNG PELEPAS")
    tech_name = st.text_input("Team Details", "Daus Works")
    client_name = st.text_input("Client Name", "NAZAME")
    report_dt = st.date_input("Date", datetime.now()).strftime("%d/%m/%Y")

# =========================================================
# 5. RENDER UTAMA (UI CHECKLIST / DOCUMENT)
# =========================================================
checklist_results = []
document_results = []
st.header(f"📋 {selected_template}")

if config.get("type") == "document":
    for sec_idx, sec_data in enumerate(config["content"]):
        heading = sec_data.get("heading", f"Section {sec_idx + 1}")
        with st.expander(heading, expanded=True):
            e_heading = st.text_input("Section Heading", value=heading, key=f"doc_h_{sec_idx}")

            e_paras = []
            for p_idx, p_val in enumerate(sec_data.get("paragraphs", [])):
                p_text = st.text_area(f"Paragraph {p_idx+1}", value=p_val, key=f"doc_p_{sec_idx}_{p_idx}", height=80)
                e_paras.append(p_text)

            e_bullets = []
            if "bullets" in sec_data:
                st.markdown("**Bullet Points**")
                for b_idx, b_val in enumerate(sec_data.get("bullets", [])):
                    b_text = st.text_input(f"Bullet {b_idx+1}", value=b_val, key=f"doc_b_{sec_idx}_{b_idx}")
                    e_bullets.append(b_text)

            e_numbered = []
            if "numbered" in sec_data:
                st.markdown("**Numbered Items**")
                for n_idx, n_val in enumerate(sec_data.get("numbered", [])):
                    n_text = st.text_input(f"Item {n_idx+1}", value=n_val, key=f"doc_num_{sec_idx}_{n_idx}")
                    e_numbered.append(n_text)

            e_paras_after = []
            if "paragraphs_after" in sec_data:
                for pa_idx, pa_val in enumerate(sec_data.get("paragraphs_after", [])):
                    pa_text = st.text_area(f"Paragraph After {pa_idx+1}", value=pa_val, key=f"doc_pa_{sec_idx}_{pa_idx}", height=80)
                    e_paras_after.append(pa_text)

            document_results.append({
                "heading": e_heading,
                "paragraphs": e_paras,
                "bullets": e_bullets,
                "numbered": e_numbered,
                "paragraphs_after": e_paras_after
            })
else:
    for sec_idx, item in enumerate(config["content"]):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            sec, tasks = item[0], item[1]
            checklist_results.append({"task": sec, "res": "TITLE", "com": ""})
            with st.expander(sec, expanded=True):
                for t_idx, t in enumerate(tasks):
                    u_key = f"{sec_idx}_{t_idx}"

                    if config.get("type") == "technical":
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        c1.write(f"**{t}**")
                        spec = c2.text_input("Spec", key=f"s_{u_key}")
                        act = c3.text_input("Actual", key=f"a_{u_key}")
                        res = c4.selectbox("Result", ["PASS", "FAIL", "N/A"], key=f"r_{u_key}")
                        checklist_results.append({"task": t, "res": res, "spec": spec, "actual": act})
                    else:
                        c1, c2, c3 = st.columns([1, 1, 2])
                        res = c1.radio(t, ["PASS", "FAIL", "N/A"], key=f"rad_{u_key}", horizontal=True)
                        if t in sn_database:
                            sel = c3.selectbox("Select SN", ["Manual Input"] + sn_database[t], key=f"sel_{u_key}")
                            rem = c3.text_input("Input SN", key=f"inp_{u_key}") if sel == "Manual Input" else sel
                        else:
                            rem = c3.text_input("Remarks", key=f"rem_{u_key}")
                        checklist_results.append({"task": t, "res": res, "com": rem})

# --- SUMMARY, EVIDENCE & SIG ---
if 'issue_list' not in st.session_state:
    st.session_state['issue_list'] = []

st.divider()
st.header("⚠️ SUMMARY & ISSUES")
for i, item in enumerate(st.session_state['issue_list']):
    c1, c2 = st.columns(2)
    st.session_state['issue_list'][i]['issue'] = c1.text_area(f"Issue {i+1}", item['issue'], key=f"is_{i}")
    st.session_state['issue_list'][i]['Remarks'] = c2.text_area(f"Remarks {i+1}", item['Remarks'], key=f"ac_{i}")

if st.button("➕ Add Issue"):
    st.session_state['issue_list'].append({'issue': '', 'Remarks': ''})
    st.rerun()

st.divider()
st.header("🖼️ EVIDENCE")
u_files = st.file_uploader("Upload Evidence", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
evidence_data = []
if u_files:
    cols = st.columns(4)
    for idx, f in enumerate(u_files):
        with cols[idx % 4]:
            st.image(f, use_container_width=True)
            cap = st.text_input(f"Caption {idx+1}", f"Evidence {idx+1}", key=f"cap_{idx}")
            evidence_data.append({"file": f, "label": cap})

st.divider()
st.header("✍️ APPROVAL")
ca, cb = st.columns(2)
with ca:
    st.write("Prepared By:")
    sig1 = st_canvas(stroke_width=2, height=150, width=300, key="sig1", background_color="#ffffff")
with cb:
    st.write("Verified By:")
    sig2 = st_canvas(stroke_width=2, height=150, width=300, key="sig2", background_color="#ffffff")

# =========================================================
# 6. PDF GENERATION WITH SESSION STATE PRESERVATION
# =========================================================
st.divider()

def on_click_generate():
    st.session_state["trigger_pdf_generate"] = True

st.button("🚀 GENERATE FINAL REPORT", type="primary", use_container_width=True, on_click=on_click_generate)

if st.session_state.get("trigger_pdf_generate", False):
    st.session_state["trigger_pdf_generate"] = False
    with st.spinner("Jana Laporan PDF... Sila tunggu..."):
        temp_files_to_delete = []
        try:
            p_img, v_img = None, None

            try:
                if sig1 is not None and sig1.image_data is not None:
                    p_img = process_signature(sig1.image_data)
            except Exception:
                p_img = None

            try:
                if sig2 is not None and sig2.image_data is not None:
                    v_img = process_signature(sig2.image_data)
            except Exception:
                v_img = None

            if p_img is None:
                p_img = Image.new("RGB", (300, 150), (255, 255, 255))
            if v_img is None:
                v_img = Image.new("RGB", (300, 150), (255, 255, 255))

            pdf = VTMS_Full_Report(header_title=header_txt)
            logo_to_use = FIXED_LOGO_PATH if os.path.exists(FIXED_LOGO_PATH) else None

            # 1. Cover Page
            pdf.cover_page({
                "owner": sys_owner,
                "ref": proj_ref,
                "title": selected_template,
                "loc": loc,
                "id": doc_id,
                "dt": report_dt
            }, logo_path=logo_to_use)

            # 2. Table of Contents
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "TABLE OF CONTENTS", 0, 1)
            pdf.ln(5)
            pdf.set_font('Arial', '', 11)
            toc_items = [
                ("2.0", "DETAILS / CONTENT"),
                ("3.0", "SUMMARY & ISSUES"),
                ("4.0", "APPROVAL"),
                ("5.0", "ATTACHMENTS")
            ]
            for n, t in toc_items:
                pdf.cell(10, 10, n, 0, 0)
                pdf.cell(0, 10, t, 0, 1)

            # 3. Content (Document vs Checklist)
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "2.0    DETAILS / CONTENT", 0, 1)
            pdf.ln(2)

            if config.get("type") == "document":
                for d_item in document_results:
                    if pdf.get_y() > 250:
                        pdf.add_page()

                    if d_item.get("heading"):
                        pdf.set_font('Arial', 'B', 10)
                        pdf.multi_cell(0, 6, clean_text(d_item["heading"]), 0, 'L')
                        pdf.ln(1)

                    pdf.set_font('Arial', '', 9)
                    for p in d_item.get("paragraphs", []):
                        if p.strip():
                            pdf.multi_cell(0, 5, clean_text(p), 0, 'L')
                            pdf.ln(2)

                    for b in d_item.get("bullets", []):
                        if b.strip():
                            pdf.set_x(15)
                            pdf.multi_cell(0, 5, f"-  {clean_text(b)}", 0, 'L')

                    if d_item.get("bullets"):
                        pdf.ln(2)

                    for n_idx, num_str in enumerate(d_item.get("numbered", []), 1):
                        if num_str.strip():
                            pdf.set_x(15)
                            pdf.multi_cell(0, 5, f"{n_idx}.  {clean_text(num_str)}", 0, 'L')

                    if d_item.get("numbered"):
                        pdf.ln(2)

                    for pa in d_item.get("paragraphs_after", []):
                        if pa.strip():
                            pdf.multi_cell(0, 5, clean_text(pa), 0, 'L')
                            pdf.ln(2)

                    pdf.ln(3)

            else:
                h_l, w_l = config.get("headers", ["NO", "ITEM", "PASS", "FAIL", "REMARK"]), config.get("widths", [10, 110, 15, 15, 40])
                pdf.set_font('Arial', 'B', 8)
                pdf.set_fill_color(230, 230, 230)
                for i, h in enumerate(h_l):
                    pdf.cell(w_l[i], 8, clean_text(h), 1, 0, 'C', 1)
                pdf.ln()

                cnt = 1
                for row in checklist_results:
                    if row['res'] == "TITLE":
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(sum(w_l), 8, f" {clean_text(row['task'])}", 1, 1, 'L', 1)
                        cnt = 1
                    else:
                        pdf.set_font('Arial', '', 7)
                        txt_remark = clean_text(row.get('com', ''))

                        lines = pdf_split_lines(pdf, w_l[4], txt_remark)
                        line_count = len(lines)
                        row_h = max(8, line_count * 5)

                        if pdf.get_y() + row_h > 270:
                            pdf.add_page()
                            pdf.set_font('Arial', 'B', 8)
                            pdf.set_fill_color(230, 230, 230)
                            for i, h in enumerate(h_l):
                                pdf.cell(w_l[i], 8, clean_text(h), 1, 0, 'C', 1)
                            pdf.ln()
                            pdf.set_font('Arial', '', 7)

                        curr_x = pdf.get_x()
                        curr_y = pdf.get_y()

                        pdf.cell(w_l[0], row_h, str(cnt), 1, 0, 'C')
                        pdf.cell(w_l[1], row_h, f" {clean_text(row['task'])}", 1, 0, 'L')

                        if config.get("type") == "technical":
                            pdf.cell(w_l[2], row_h, clean_text(row.get('spec', '-')), 1, 0, 'C')
                            pdf.cell(w_l[3], row_h, clean_text(row.get('actual', '-')), 1, 0, 'C')
                            pdf.cell(w_l[4], row_h, clean_text(row['res']), 1, 0, 'C')
                        else:
                            pdf.cell(w_l[2], row_h, "X" if row['res'] == "PASS" else "", 1, 0, 'C')
                            pdf.cell(w_l[3], row_h, "X" if row['res'] == "FAIL" else "", 1, 0, 'C')

                            pdf.set_xy(curr_x + w_l[0] + w_l[1] + w_l[2] + w_l[3], curr_y)
                            pdf.cell(w_l[4], row_h, "", 1, 0)
                            pdf.set_xy(curr_x + w_l[0] + w_l[1] + w_l[2] + w_l[3], curr_y + (row_h - (line_count * 5)) / 2)
                            pdf.multi_cell(w_l[4], 5, txt_remark, 0, 'L')

                        pdf.set_xy(curr_x, curr_y + row_h)
                        cnt += 1

            # 4. Summary & Issues
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "3.0    SUMMARY & ISSUES", 0, 1)

            w_issue = [15, 85, 90]
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(w_issue[0], 10, "NO", 1, 0, 'C', 1)
            pdf.cell(w_issue[1], 10, "SUMMARY / ISSUES", 1, 0, 'C', 1)
            pdf.cell(w_issue[2], 10, "REMARKS", 1, 1, 'C', 1)

            pdf.set_font('Arial', '', 8)
            for idx, item in enumerate(st.session_state['issue_list']):
                txt_issue = clean_text(item['issue'])
                txt_remark = clean_text(item['Remarks'])

                lines_issue = pdf_split_lines(pdf, w_issue[1], txt_issue)
                lines_remark = pdf_split_lines(pdf, w_issue[2], txt_remark)

                max_lines = max(len(lines_issue), len(lines_remark))
                row_h = max(10, max_lines * 5)

                if pdf.get_y() + row_h > 270:
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(230, 230, 230)
                    pdf.cell(w_issue[0], 10, "NO", 1, 0, 'C', 1)
                    pdf.cell(w_issue[1], 10, "SUMMARY / ISSUES", 1, 0, 'C', 1)
                    pdf.cell(w_issue[2], 10, "REMARKS", 1, 1, 'C', 1)
                    pdf.set_font('Arial', '', 8)

                curr_x = pdf.get_x()
                curr_y = pdf.get_y()

                pdf.cell(w_issue[0], row_h, str(idx + 1), 1, 0, 'C')

                pdf.cell(w_issue[1], row_h, "", 1, 0)
                pdf.set_xy(curr_x + w_issue[0], curr_y + (row_h - len(lines_issue) * 5) / 2)
                pdf.multi_cell(w_issue[1], 5, txt_issue, 0, 'L')

                pdf.set_xy(curr_x + w_issue[0] + w_issue[1], curr_y)
                pdf.cell(w_issue[2], row_h, "", 1, 0)
                pdf.set_xy(curr_x + w_issue[0] + w_issue[1], curr_y + (row_h - len(lines_remark) * 5) / 2)
                pdf.multi_cell(w_issue[2], 5, txt_remark, 0, 'L')

                pdf.set_xy(curr_x, curr_y + row_h)

            # 5. Approval
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "4.0    APPROVAL & ACCEPTANCE", 0, 1)
            pdf.ln(5)
            pdf.set_font('Arial', '', 10)
            stmt = "The undersigned hereby confirms that the works described in this report have been carried out in accordance with agreed scope."
            pdf.multi_cell(0, 6, stmt, 0, 'L')

            tmp_p = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            p_path = tmp_p.name
            tmp_p.close()
            p_img.save(p_path)
            temp_files_to_delete.append(p_path)

            tmp_v = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            v_path = tmp_v.name
            tmp_v.close()
            v_img.save(v_path)
            temp_files_to_delete.append(v_path)

            y_sig = pdf.get_y() + 10
            pdf.image(p_path, x=40, y=y_sig, w=40)
            pdf.image(v_path, x=130, y=y_sig, w=40)
            pdf.set_y(y_sig + 25)

            myt_now = datetime.now(timezone.utc) + timedelta(hours=8)
            gen_timestamp = myt_now.strftime("%d/%m/%Y %H:%M:%S")

            pdf.set_font('Arial', 'B', 10)
            pdf.set_x(15)
            pdf.cell(90, 8, f"PREPARED BY: {clean_text(tech_name)}", 0, 0, 'C')
            pdf.set_x(105)
            pdf.cell(90, 8, f"VERIFIED BY: {clean_text(client_name)}", 0, 1, 'C')
            pdf.set_font('Arial', 'I', 8)
            pdf.set_x(15)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 0, 'C')
            pdf.set_x(105)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 1, 'C')

            # 6. Attachments
            if evidence_data:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "5.0    ATTACHMENTS", 0, 1)
                pdf.ln(5)

                if "SERVER REPORT" in selected_template:
                    for i, ev in enumerate(evidence_data):
                        if i > 0 and i % 2 == 0:
                            pdf.add_page()

                        pos_in_page = i % 2
                        x = 30
                        y = 35 if pos_in_page == 0 else 145

                        processed_img = process_image(ev['file'])
                        if processed_img:
                            tmp_ev = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                            temp_ev_path = tmp_ev.name
                            tmp_ev.close()
                            processed_img.save(temp_ev_path, "JPEG")
                            temp_files_to_delete.append(temp_ev_path)

                            pdf.rect(x, y, 150, 100)
                            pdf.image(temp_ev_path, x=x + 2, y=y + 2, w=145, h=90)
                            pdf.set_xy(x, y + 95)
                            pdf.set_font('Arial', 'B', 10)
                            pdf.multi_cell(150, 6, clean_text(ev['label']), 0, 'C')
                else:
                    for i, ev in enumerate(evidence_data):
                        if i > 0 and i % 4 == 0:
                            pdf.add_page()
                        pos = i % 4
                        x, y = [20, 110][pos % 2], [40, 145][pos // 2]

                        processed_img = process_image(ev['file'])
                        if processed_img:
                            tmp_ev = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                            temp_ev_path = tmp_ev.name
                            tmp_ev.close()
                            processed_img.save(temp_ev_path, "JPEG")
                            temp_files_to_delete.append(temp_ev_path)

                            pdf.rect(x, y, 80, 80)
                            pdf.image(temp_ev_path, x=x + 2, y=y + 2, w=76, h=60)
                            pdf.set_xy(x, y + 65)
                            pdf.set_font('Arial', '', 9)
                            pdf.multi_cell(80, 5, clean_text(ev['label']), 0, 'C')

            # 7. Penyiapan Fail PDF Bytes
            final_bytes = get_pdf_bytes(pdf)
            date_str = myt_now.strftime('%d%m%Y')
            clean_filename = selected_template.replace(" ", "_")
            full_file_name = f"{clean_filename}_{date_str}.pdf"

            st.session_state["pdf_bytes"] = final_bytes
            st.session_state["pdf_filename"] = full_file_name
            st.session_state["pdf_b64"] = base64.b64encode(final_bytes).decode('utf-8')
            st.success("✅ Laporan berjaya dijana!")

        except Exception as e:
            st.error(f"❌ Ralat semasa menjana PDF: {e}")
            st.exception(e)
        finally:
            for file_path in temp_files_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

# =========================================================
# 7. PAPARAN PREVIEW & DOWNLOAD
# =========================================================
if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
    st.divider()
    st.markdown("## 👁️ REPORT PREVIEW & DOWNLOAD")

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        st.download_button(
            label=f"📥 DOWNLOAD {st.session_state['pdf_filename']}",
            data=st.session_state["pdf_bytes"],
            file_name=st.session_state["pdf_filename"],
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

    with col_btn2:
        new_tab_js = f"""
            <script>
                function openPDF() {{
                    var pdfData = "data:application/pdf;base64,{st.session_state['pdf_b64']}";
                    var win = window.open();
                    win.document.write('<iframe src="' + pdfData + '" frameborder="0" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;" allowfullscreen></iframe>');
                }}
            </script>
            <button onclick="openPDF()" style="width:100%; background-color:#2e7bcf; color:white; padding:10px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; height:42px;">
                🔗 PREVIEW REPORT IN NEW TAB
            </button>
        """
        st.components.v1.html(new_tab_js, height=50)

    pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{st.session_state['pdf_b64']}" 
            width="100%" 
            height="800px" 
            type="application/pdf"
            style="border: 2px solid #ccc; border-radius: 8px;">
        </iframe>
    '''
    st.components.v1.html(pdf_display, height=820)
