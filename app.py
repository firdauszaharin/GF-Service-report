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
        "RADAR INTERFACE SERVICE REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1.0 TERMA SCANTER 5202 - General Inspection", [
                    "Physical condition inspection",
                    "Check equipment for physical damage",
                    "Check connector condition",
                    "Check cable condition",
                    "Check error / alarm indication"
                ]],
                ["2.0 ACP - Azimuth Change Pulse", [
                    "Check ACP output signal",
                    "Verify waveform using oscilloscope",
                    "Measure frequency",
                    "Measure period",
                    "Verify ACP pulse count / revolution",
                    "Calculate antenna RPM",
                    "Compare RPM with R5 RIC indication"
                ]],
                ["3.0 ARP - Azimuth Reference Pulse", [
                    "Check ARP output signal",
                    "Verify waveform using oscilloscope",
                    "Verify 1 pulse / revolution",
                    "Measure pulse period",
                    "Verify signal consistency with ACP"
                ]],
                ["4.0 Analogue Video", [
                    "Check Analogue Video output",
                    "Verify video waveform using oscilloscope",
                    "Measure output voltage",
                    "Verify output frequency / waveform",
                    "Verify output impedance / termination",
                    "Confirm 50 ohm / 75 ohm configuration with OEM",
                    "Verify signal suitable for R5 RIC input"
                ]],
                ["5.0 Trigger", [
                    "Check Trigger output signal",
                    "Verify waveform using oscilloscope",
                    "Measure trigger voltage",
                    "Measure trigger frequency",
                    "Verify rising / falling edge",
                    "Verify trigger level against OEM specification",
                    "Verify termination / measurement arrangement"
                ]],
                ["6.0 Oscilloscope Measurement Setup", [
                    "Verify oscilloscope probe setting",
                    "Verify oscilloscope coupling setting",
                    "Verify Volt/Div setting",
                    "Verify Time/Div setting",
                    "Verify trigger setting",
                    "Verify measurement termination",
                    "Record measured values"
                ]],
                ["7.0 Saab R5 RIC Interface Verification", [
                    "Verify ACP input",
                    "Verify ARP input",
                    "Verify Video input",
                    "Verify Trigger input",
                    "Verify signal indication at R5 RIC",
                    "Verify antenna RPM indication",
                    "Verify pulse rate indication"
                ]],
                ["8.0 Integration / Data Verification", [
                    "Verify radar data received at R5 RIC",
                    "Verify azimuth data",
                    "Verify video data",
                    "Verify trigger synchronization",
                    "Verify radar data output to Radar Extractor",
                    "Perform end-to-end data verification"
                ]],
                ["9.0 Cable & Connector", [
                    "Inspect BNC connector",
                    "Inspect coaxial cable",
                    "Verify cable impedance",
                    "Verify cable continuity",
                    "Check connector termination",
                    "Check cable identification / labelling"
                ]],
                ["10.0 Final Verification", [
                    "Review all measured values",
                    "Record outstanding issues",
                    "Confirm OEM clarification required",
                    "Confirm equipment returned to normal configuration",
                    "Housekeeping"
                ]]
            ]
        },
        "MET REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1.0 Anderaa Smartguard Datalogger", ["No physical defect, no error/alarm", "Check SN :1182", "Sensor detection check", "Data Storage Capacity/Backup check"]],
                ["2.0 AMEC Mando 303 Transponder", ["No physical defect, no error/alarm", "Transmit AIS msg8 check", "Check SN :B4K300007", "Verify data at VTS Control(Coastwatch)"]],
                ["3.0 Vaisala PWD20 Visibility Sensor", ["No physical defect, no error/alarm", "Check SN :W4017603", "Monitor Data Output", "Inspect Cables", "Cleaning sensor"]],
                ["4.0 Vaisala WXT536 Weather Sensor", ["No physical defect, no error/alarm", "Check SN : W4045971", "Monitor Data Output", "Inspect Cables", "Cleaning sensor"]],
                ["5.0 Solar Panel 12V 100Watt", ["No physical defect", "Voltage Output check (Remaks voltage)", "Cleaning"]],
                ["6.0 Phocos Solar Charger Controller", ["No physical defect, no error/alarm"]],
                ["7.0 MSB 12V 100Ah AGM Battery", ["No physical defect", "Voltage Output check (Remarks voltage)"]],
                ["8.0 VHF Antenna", ["No physical defect"]],
                ["9.0 GPS Antenna", ["No physical defect"]],
                ["10.0 Stainless Equipment Enclosure", ["No physical defect"]],
                ["11.0 Housekeeping", ["Remove dust on cable terminals"]]
            ]
        },
        "OPERATOR WORKSTATION REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1.0 HP Z2 TWR Workstation", ["No physical defect", "Check SN :", "Network test (Note IP in Remark)", "Check system/Windows update"]],
                ["2.0 Monitor HP P34hc G4", ["No physical defect", "Monitor 1 Check SN :", "Monitor 2 Check SN :"]],
                ["3.0 HP Wireless Keyboard & Mouse", ["No physical defect", "Function test"]],
                ["4.0 Coastwatch Dongle", ["No physical defect", "Check ID(*localhost 127.0.0.1 1947) :"]],
                ["5.0 UPS ENPLUSEVOIIX-2KTS", ["No physical defect", "Check SN :", "Check output 230 VAC", "Battery test / Backup time"]],
                ["6.0 Operator Terminal CYS1702", ["No physical defect", "Check SN :", "Network test (Note IP in Remark)", "TX/RX Check (Radio test)", "Playback voice check", "Event log record"]],
                ["7.0 Monitor LIYAMA PROLITE", ["No physical defect", "Check SN :"]],
                ["8.0 Headset - PLATORA", ["No physical defect"]],
                ["9.0 Microphone PTT CYS1102", ["No physical defect", "Check SN :"]],
                ["10.0 Foot Pedal CYS1315", ["No physical defect", "Check SN :"]],
                ["11.0 Handset PTT CYS1313", ["No physical defect", "Check SN :"]],
                ["12.0 Bluetooth Headset AINA", ["No physical defect", "Check ID (Note in Remark)", "Check SN:"]],
                ["13.0 Software Check", ["Coastwatch properly installed", "Software functioning", "Receiving AIS data", "Database/Playback search test", "Check 3D GeoVS (PTP 3D only)"]],
                ["14.0 Housekeeping", ["Remove dust on cables/fans"]]
            ]
        },
        "WALL DISPLAY REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["Displays", [f"Wall Display-{i}" for i in range(1, 16)]],
                ["Housekeeping", ["Remove dust on cables"]]
            ]
        },
        "VHF PTP FLOOR 8": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["Passive Components", ["Antenna Omnidirectional", "Lightning protector", "Coaxial cable", "Check VSWR (Note in remark)", "VHF splitter", "VHF Combiner"]],
                ["VHF Basestation", ["VHF 1 Check SN : 0001", "VHF 2 Check SN : 0002", "VHF 3 Check SN : 0003", "VHF 4 Check SN : 0004", "VHF 5 Check SN : 0005", "VHF 6 Check SN : 0006"]],
                ["Network ", ["Switch Cisco Catalyst", "NTP Time Server", "Check NTP Monitoring Web", "Lease line & SDWAN Equipment"]],
                ["Housekeeping", ["Remove dust on terminals"]]
            ]
        },
        "PTP SERVER REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["PTP PPB SERVER", ["App Server VTSA SN: SGH443KXBB", "Database Server SN: SGH443KXBN", "Sensor Server SN: SGH443KX9Z", "VHF Server 1 SN: 8CJX034", "VHF Server 2 SN: 2JNX034"]],
                ["STORAGE & SWITCH", ["SAN Switch SN: CZC4329XHM/XHP", "SAN Storage MSA SN: ACV411W1WL", "KVM LCD8500 SN: 2C4426BADY"]],
                ["SERVER TASKS", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", " Restart services or applications if necessary"]],
                ["CHECK SERVER PERFORMANCE", ["CPU usage (App Server VTSA)", "CPU usage (Database Server)", "CPU usage (Sensor Server)", "RAM usage (App Server VTSA)", "RAM usage (Database Server)", "RAM usage (Sensor Server)", "Windows update (App Server VTSA)", "Windows update (Database Server)", "Windows update (Sensor Server)"]],
                ["HOUSEKEEPING", ["Remove dust on terminals"]]
            ]
        },
        "LPJ SERVER REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["LPJ SERVER", ["App/DB Server SN: SGH441G81Z"]],
                ["STORAGE & SWITCH", ["SAN Switch SN: CZC4329XF8/XHT", "SAN Storage MSA SN: ACV411W1LS", "NTP Time Server and GPS Antenna check"]],
                ["SERVER TASKS", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", " Restart services or applications if necessary"]],
                ["CHECK SERVER PERFORMANCE", ["CPU usage", "RAM usage", "Windows update"]],
                ["HOUSEKEEPING", ["Remove dust on terminals"]]
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
        with open(TEMPLATE_FILE, 'w') as f:
            json.dump(defaults, f, indent=4)

    if os.path.exists(TAMBAHAN_FILE):
        try:
            with open(TAMBAHAN_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return defaults

if 'all_templates' not in st.session_state:
    st.session_state['all_templates'] = load_templates()

def save_templates_to_file():
    with open(TAMBAHAN_FILE, 'w') as f:
        json.dump(st.session_state['all_templates'], f, indent=4)

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
    text = "" if text is None else str(text)
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

class VTMS_Full_Report(FPDF):
    def __init__(self, header_title=""):
        super().__init__()
        self.header_title = header_title
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
        self.multi_cell(0, 8, data['owner'].upper(), 0, 'C')
        self.ln(10)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "PROJECT REFERENCE NO:", 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, data['ref'], 0, 'C')
        self.ln(25)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, "DOCUMENT TITLE:", 0, 1, 'C')
        self.set_font('Arial', 'B', 22)
        self.multi_cell(0, 12, data['title'].upper(), 0, 'C')
        self.ln(35)
        for k, v in [("LOCATION", data['loc']), ("DOCUMENT ID", data['id']), ("DATE", data['dt'])]:
            self.set_x(35)
            self.set_font('Arial', 'B', 11)
            self.cell(50, 12, k, 1, 0, 'L')
            self.set_font('Arial', '', 11)
            self.cell(90, 12, v, 1, 1, 'L')

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
        n_type = st.radio("Format", ["checkbox", "technical"])
        if st.button("Build Template"):
            if n_name:
                h_l = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"] if n_type == "checkbox" else ["NO", "ITEM", "SPEC", "ACTUAL", "RESULT"]
                w_l = [10, 110, 15, 15, 40] if n_type == "checkbox" else [10, 75, 40, 40, 25]
                st.session_state['all_templates'][n_name] = {"headers": h_l, "widths": w_l, "type": n_type, "content": [["1.0 DETAILS", ["First Item"]]]}
                save_templates_to_file()
                st.rerun()

    st.divider()
    selected_template = st.selectbox("Template Type:", list(st.session_state['all_templates'].keys()))

    with st.expander("📝 EDIT SECTION / TASKS"):
        st.subheader("Manage Sections")
        new_sec = st.text_input("New Section Name")
        col1, col2 = st.columns(2)
        if col1.button("➕ Add Section"):
            if new_sec:
                st.session_state['all_templates'][selected_template]["content"].append([new_sec, ["New Item"]])
                save_templates_to_file()
                st.rerun()

        sec_names = [s[0] for s in st.session_state['all_templates'][selected_template]["content"]]
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
            if s[0] == target_sec:
                current_tasks = s[1]
                break

        new_t_name = st.text_input("New Task Name")
        col3, col4 = st.columns(2)
        if col3.button("➕ Add Task"):
            if new_t_name and target_sec:
                for item in st.session_state['all_templates'][selected_template]["content"]:
                    if item[0] == target_sec:
                        item[1].append(new_t_name)
                        break
                save_templates_to_file()
                st.rerun()

        target_task_del = st.selectbox("Select Task to Delete", current_tasks if current_tasks else [""])
        if col4.button("🗑️ Delete Task"):
            if target_task_del and target_sec:
                for item in st.session_state['all_templates'][selected_template]["content"]:
                    if item[0] == target_sec:
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

# --- Render Checklist ---
config = st.session_state['all_templates'][selected_template]
checklist_results = []
st.header(f"📋 {selected_template}")

for sec_idx, (sec, tasks) in enumerate(config["content"]):
    checklist_results.append({"task": sec, "res": "TITLE", "com": ""})
    with st.expander(sec, expanded=True):
        for t_idx, t in enumerate(tasks):
            u_key = f"{sec_idx}_{t_idx}"

            if config["type"] == "technical":
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
# 5. PDF GENERATION WITH SESSION STATE PRESERVATION
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
                ("2.0", "DETAILS / CHECKLIST"),
                ("3.0", "SUMMARY & ISSUES"),
                ("4.0", "APPROVAL"),
                ("5.0", "ATTACHMENTS")
            ]
            for n, t in toc_items:
                pdf.cell(10, 10, n, 0, 0)
                pdf.cell(0, 10, t, 0, 1)

            # 3. Checklist
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "2.0    DETAILS / CHECKLIST", 0, 1)

            h_l, w_l = config["headers"], config["widths"]
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(230, 230, 230)
            for i, h in enumerate(h_l):
                pdf.cell(w_l[i], 8, h, 1, 0, 'C', 1)
            pdf.ln()

            cnt = 1
            for row in checklist_results:
                if row['res'] == "TITLE":
                    pdf.set_font('Arial', 'B', 8)
                    pdf.set_fill_color(245, 245, 245)
                    pdf.cell(sum(w_l), 8, f" {row['task']}", 1, 1, 'L', 1)
                    cnt = 1
                else:
                    pdf.set_font('Arial', '', 7)
                    txt_remark = str(row.get('com', ''))

                    lines = pdf_split_lines(pdf, w_l[4], txt_remark)
                    line_count = len(lines)
                    row_h = max(8, line_count * 5)

                    if pdf.get_y() + row_h > 270:
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 8)
                        pdf.set_fill_color(230, 230, 230)
                        for i, h in enumerate(h_l):
                            pdf.cell(w_l[i], 8, h, 1, 0, 'C', 1)
                        pdf.ln()
                        pdf.set_font('Arial', '', 7)

                    curr_x = pdf.get_x()
                    curr_y = pdf.get_y()

                    pdf.cell(w_l[0], row_h, str(cnt), 1, 0, 'C')
                    pdf.cell(w_l[1], row_h, f" {row['task']}", 1, 0, 'L')

                    if config.get("type") == "technical":
                        pdf.cell(w_l[2], row_h, str(row.get('spec', '-')), 1, 0, 'C')
                        pdf.cell(w_l[3], row_h, str(row.get('actual', '-')), 1, 0, 'C')
                        pdf.cell(w_l[4], row_h, str(row['res']), 1, 0, 'C')
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
                txt_issue = str(item['issue'])
                txt_remark = str(item['Remarks'])

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

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p:
                p_path = tmp_p.name
            p_img.save(p_path)
            temp_files_to_delete.append(p_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_v:
                v_path = tmp_v.name
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
            pdf.cell(90, 8, f"PREPARED BY: {tech_name}", 0, 0, 'C')
            pdf.set_x(105)
            pdf.cell(90, 8, f"VERIFIED BY: {client_name}", 0, 1, 'C')
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
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_ev:
                                temp_ev_path = tmp_ev.name
                            processed_img.save(temp_ev_path, "JPEG")
                            temp_files_to_delete.append(temp_ev_path)

                            pdf.rect(x, y, 150, 100)
                            pdf.image(temp_ev_path, x=x + 2, y=y + 2, w=145, h=90)
                            pdf.set_xy(x, y + 95)
                            pdf.set_font('Arial', 'B', 10)
                            pdf.multi_cell(150, 6, ev['label'], 0, 'C')
                else:
                    for i, ev in enumerate(evidence_data):
                        if i > 0 and i % 4 == 0:
                            pdf.add_page()
                        pos = i % 4
                        x, y = [20, 110][pos % 2], [40, 145][pos // 2]

                        processed_img = process_image(ev['file'])
                        if processed_img:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_ev:
                                temp_ev_path = tmp_ev.name
                            processed_img.save(temp_ev_path, "JPEG")
                            temp_files_to_delete.append(temp_ev_path)

                            pdf.rect(x, y, 80, 80)
                            pdf.image(temp_ev_path, x=x + 2, y=y + 2, w=76, h=60)
                            pdf.set_xy(x, y + 65)
                            pdf.set_font('Arial', '', 9)
                            pdf.multi_cell(80, 5, ev['label'], 0, 'C')

            # 7. Penyiapan Fail PDF Bytes
            raw_output = pdf.output()
            final_bytes = bytes(raw_output) if isinstance(raw_output, (bytes, bytearray)) else str(raw_output).encode('latin-1')

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
# 6. PAPARAN PREVIEW & DOWNLOAD
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
