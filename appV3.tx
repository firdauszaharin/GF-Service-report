import streamlit as st
from fpdf import FPDF
import os
import json
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageOps
import numpy as np
from streamlit_drawable_canvas import st_canvas

# --- 1. SECURITY CHECK (Sistem Password) ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "DausVTMS2026": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.header("🔒 Akses Terhad")
        st.text_input("Sila Masukkan Password Akses", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.header("🔒 Akses Terhad")
        st.text_input("Sila Masukkan Password Akses", type="password", on_change=password_entered, key="password")
        st.error("😕 Password salah. Sila hubungi pentadbir sistem.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 1. PENGURUSAN TEMPLATE ---
TEMPLATE_FILE = 'templates.json'
TAMBAHAN_FILE = 'templates_tambahan.json' # Fail simpanan untuk perubahan (Add/Delete)

def load_templates():
    # 1. Load default dari kod jika fail templates.json tak wujud
    defaults = {
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
                ["3.0 HP Wireless Keyboard & Mouse", ["No physical defect","Function test"]],
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
                ["PTP PPB Servers", ["App Server VTSA SN: SGH443KXBB", "Database Server SN: SGH443KXBN", "Sensor Server SN: SGH443KX9Z", "VHF Server 1 SN: 8CJX034", "VHF Server 2 SN: 2JNX034"]],
                ["Storage & Switch", ["SAN Switch SN: CZC4329XHM/XHP", "SAN Storage MSA SN: ACV411W1WL", "KVM LCD8500 SN: 2C4426BADY"]],
                ["Server Tasks", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", " Restart services or applications if necessary"]],
                ["Housekeeping", ["Remove dust on terminals"]]
            ]
        },
            "LPJ SERVER REPORT": {
            "headers": ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["LPJ Servers", ["App/DB Server SN: SGH441G81Z"]],
                ["Storage & Switch", [ "SAN Switch SN: CZC4329XF8/XHT", "SAN Storage MSA SN: ACV411W1LS", "NTP Time Server and GPS Antenna check"]],
                ["Server Tasks", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", " Restart services or applications if necessary"]],
                ["Housekeeping", ["Remove dust on terminals"]]
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
            "headers": ["NO", "ITEM / ACTIVITY","PASS", "FAIL", "REMARK"],
            "widths": [10, 110, 15, 15, 40],
            "type": "checkbox",
            "content": [
                ["1. Inspection", ["Visual inspection", "Physical check", "Power Status"]],
                ["2. Analysis", ["Root Cause (Hardware/Network)", "External Factors"]],
                ["3. Action Taken", ["Repair / Replacement", "Configuration / Restoration", "System Testing"]]
            ]
        }
    }

    # Cipta fail asal jika tiada (untuk rujukan sahaja)
    if not os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'w') as f:
            json.dump(defaults, f, indent=4)

    # 2. Keutamaan: Baca fail TAMBAHAN jika wujud (ini mengandungi Add/Delete terbaru)
    if os.path.exists(TAMBAHAN_FILE):
        with open(TAMBAHAN_FILE, 'r') as f:
            return json.load(f)
    
    # 3. Jika fail tambahan tiada, guna defaults
    return defaults

if 'all_templates' not in st.session_state:
    st.session_state['all_templates'] = load_templates()

def save_templates_to_file():
    # HANYA simpan ke fail tambahan. Fail asal (TEMPLATE_FILE) tidak akan disentuh.
    with open(TAMBAHAN_FILE, 'w') as f:
        json.dump(st.session_state['all_templates'], f, indent=4)

# --- 2. DATABASE S/N ASAL ---
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

# --- 3. PROSES IMEJ & PDF CLASS ---
def process_image(img_input, target_size=(800, 600)):
    """Fungsi untuk memproses gambar Evidence"""
    if img_input is None: return None
    try:
        img = Image.open(img_input).convert("RGBA")
        background = Image.new("RGB", target_size, (255, 255, 255))
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        background.paste(img, offset, mask=img.split()[3] if img.mode == 'RGBA' else None)
        return background
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def process_signature(img_input):
    """Menukar data kanvas kepada imej PIL yang bersih"""
    if img_input is not None:
        try:
            # Pastikan img_input adalah numpy array dari st_canvas
            img = Image.fromarray(img_input.astype('uint8'))
            alpha = img.split()[-1]
            bbox = alpha.getbbox()
            if bbox:
                img = img.crop(bbox)
            
            new_img = Image.new("RGB", img.size, (255, 255, 255))
            new_img.paste(img, mask=img.split()[-1])
            return new_img
        except Exception as e:
            # Jika img_input bukan array atau ralat lain
            return None
    return None
class VTMS_Full_Report(FPDF):
    def __init__(self, header_title=""):
        super().__init__()
        self.header_title = header_title
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8); self.set_text_color(100)
            self.cell(0, 5, self.header_title, 0, 1, 'R')
            self.line(10, 15, 200, 15)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def cover_page(self, data, logo_path=None):
        self.add_page(); self.rect(5, 5, 200, 287)
        if logo_path: self.image(logo_path, x=75, y=20, w=60)
        self.set_font('Arial', 'B', 12); self.ln(65); self.cell(0, 5, "SYSTEM OWNER", 0, 1, 'C')
        self.set_font('Arial', 'B', 16); self.multi_cell(0, 8, data['owner'].upper(), 0, 'C'); self.ln(10)
        self.set_font('Arial', 'B', 10); self.cell(0, 5, "PROJECT REFERENCE NO:", 0, 1, 'C')
        self.set_font('Arial', '', 10); self.multi_cell(0, 5, data['ref'], 0, 'C'); self.ln(25)
        self.set_font('Arial', 'B', 18); self.cell(0, 10, "DOCUMENT TITLE:", 0, 1, 'C')
        self.set_font('Arial', 'B', 22); self.multi_cell(0, 12, data['title'].upper(), 0, 'C'); self.ln(35)
        for k, v in [("LOCATION", data['loc']), ("DOCUMENT ID", data['id']), ("DATE", data['dt'])]:
            self.set_x(35); self.set_font('Arial', 'B', 11); self.cell(50, 12, k, 1, 0, 'L')
            self.set_font('Arial', '', 11); self.cell(90, 12, v, 1, 1, 'L')

# --- 4. INTERFACE ---
st.set_page_config(page_title="VTMS Reporting System", layout="wide")

with st.sidebar:
    st.header("🏢 COMPANY ASSETS")
    
    # Tukar 'logo.png' kepada nama fail logo anda yang sebenar dalam folder
    FIXED_LOGO_PATH = "logo.png" 
    
    if os.path.exists(FIXED_LOGO_PATH):
        st.image(FIXED_LOGO_PATH, caption="Current Company Logo", width=150)
    else:
        st.error(f"Fail {FIXED_LOGO_PATH} tidak dijumpai dalam folder!")
    
    with st.expander("✨ CREATE NEW TEMPLATE"):
        n_name = st.text_input("Template Name")
        n_type = st.radio("Format", ["checkbox", "technical"])
        if st.button("Build Template"):
            if n_name:
                h_l = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"] if n_type=="checkbox" else ["NO", "ITEM", "SPEC", "ACTUAL", "RESULT"]
                w_l = [10, 110, 15, 15, 40] if n_type=="checkbox" else [10, 75, 40, 40, 25]
                st.session_state['all_templates'][n_name] = {"headers": h_l, "widths": w_l, "type": n_type, "content": [["1.0 DETAILS", ["First Item"]]]}
                save_templates_to_file(); st.rerun()

    st.divider()
    selected_template = st.selectbox("Template Type:", list(st.session_state['all_templates'].keys()))
    
    with st.expander("📝 EDIT SECTION / TASKS"):
        st.subheader("Manage Sections")
        new_sec = st.text_input("New Section Name")
        col1, col2 = st.columns(2)
        if col1.button("➕ Add Section"):
            if new_sec:
                st.session_state['all_templates'][selected_template]["content"].append([new_sec, ["New Item"]])
                save_templates_to_file(); st.rerun()
            
        sec_names = [s[0] for s in st.session_state['all_templates'][selected_template]["content"]]
        target_sec_del = st.selectbox("Select Section to Delete", sec_names)
        if col2.button("🗑️ Delete Section", type="secondary"):
            st.session_state['all_templates'][selected_template]["content"] = [s for s in st.session_state['all_templates'][selected_template]["content"] if s[0] != target_sec_del]
            save_templates_to_file(); st.rerun()

        st.divider()
        st.subheader("Manage Tasks")
        target_sec = st.selectbox("Select Target Section", sec_names)
        
        current_tasks = []
        for s in st.session_state['all_templates'][selected_template]["content"]:
            if s[0] == target_sec: current_tasks = s[1]; break

        new_t_name = st.text_input("New Task Name")
        col3, col4 = st.columns(2)
        if col3.button("➕ Add Task"):
            if new_t_name:
                for item in st.session_state['all_templates'][selected_template]["content"]:
                    if item[0] == target_sec: item[1].append(new_t_name); break
                save_templates_to_file(); st.rerun()
            
        target_task_del = st.selectbox("Select Task to Delete", current_tasks)
        if col4.button("🗑️ Delete Task"):
            for item in st.session_state['all_templates'][selected_template]["content"]:
                if item[0] == target_sec:
                    if target_task_del in item[1]:
                        item[1].remove(target_task_del); break
            save_templates_to_file(); st.rerun()

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
    client_name = st.text_input("Client Name", "En. Azman")
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
if 'issue_list' not in st.session_state: st.session_state['issue_list'] = []
st.divider(); st.header("⚠️ SUMMARY & ISSUES")
for i, item in enumerate(st.session_state['issue_list']):
    c1, c2 = st.columns(2)
    st.session_state['issue_list'][i]['issue'] = c1.text_area(f"Issue {i+1}", item['issue'], key=f"is_{i}")
    st.session_state['issue_list'][i]['Remarks'] = c2.text_area(f"Remarks {i+1}", item['Remarks'], key=f"ac_{i}")
if st.button("➕ Add Issue"): st.session_state['issue_list'].append({'issue':'','Remarks':''}); st.rerun()

st.divider(); st.header("🖼️ EVIDENCE")
u_files = st.file_uploader("Upload Evidence", accept_multiple_files=True, type=['png','jpg','jpeg'])
evidence_data = []
if u_files:
    cols = st.columns(4)
    for idx, f in enumerate(u_files):
        with cols[idx % 4]:
            st.image(f, use_container_width=True)
            cap = st.text_input(f"Caption {idx+1}", f"Evidence {idx+1}", key=f"cap_{idx}")
            evidence_data.append({"file": f, "label": cap})

st.divider(); st.header("✍️ APPROVAL")
ca, cb = st.columns(2)
with ca: st.write("Prepared By:"); sig1 = st_canvas(stroke_width=2, height=150, width=300, key="sig1", background_color="#ffffff")
with cb: st.write("Verified By:"); sig2 = st_canvas(stroke_width=2, height=150, width=300, key="sig2", background_color="#ffffff")

# --- 5. PDF GENERATION ---
if st.button("🚀 GENERATE FINAL REPORT",type="primary", use_container_width=True):
    # Ambil data imej dari canvas
    p_img = process_signature(sig1.image_data)
    v_img = process_signature(sig2.image_data)
    
    if p_img is None or v_img is None:
        st.error("Sila turunkan tanda tangan terlebih dahulu!")
    else:
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
        # Manual TOC mapping (kerana kita guna fpdf lama)
        toc_items = [
            ("2.0", "DETAILS / CHECKLIST"),
            ("3.0", "SUMMARY & ISSUES"),
            ("4.0", "APPROVAL"),
            ("5.0", "ATTACHMENTS")
        ]
        for n, t in toc_items:
            pdf.cell(10, 10, n, 0, 0)      # Cetak No Seksyen (cth: 2.0)
            pdf.cell(0, 10, t, 0, 1)       # Cetak Tajuk Seksyen (cth: DETAILS / CHECKLIST)
        

        # 3. Details / Checklist
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "2.0    DETAILS / CHECKLIST", 0, 1)
        h_l, w_l = config["headers"], config["widths"]
        pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(230, 230, 230)
        for i, h in enumerate(h_l): pdf.cell(w_l[i], 8, h, 1, 0, 'C', 1)
        pdf.ln()

        cnt = 1
        for row in checklist_results:
            if pdf.get_y() > 260: # Threshold untuk page break
                pdf.add_page()
                for i, h in enumerate(h_l): pdf.cell(w_l[i], 8, h, 1, 0, 'C', 1)
                pdf.ln()
            if row['res'] == "TITLE":
                cnt = 1; pdf.set_font('Arial', 'B', 8); pdf.set_fill_color(245, 245, 245)
                pdf.cell(sum(w_l), 7, f" {row['task']}", 1, 1, 'L', 1)
            else:
                pdf.set_font('Arial', '', 7)
                pdf.cell(w_l[0], 6, str(cnt), 1, 0, 'C')
                pdf.cell(w_l[1], 6, f" {row['task']}", 1, 0, 'L')
                if config["type"] == "technical":
                    pdf.cell(w_l[2], 6, str(row.get('spec','-')), 1, 0, 'C')
                    pdf.cell(w_l[3], 6, str(row.get('actual','-')), 1, 0, 'C')
                    pdf.cell(w_l[4], 6, row['res'], 1, 1, 'C')
                else:
                    pdf.cell(w_l[2], 6, "X" if row['res'] == "PASS" else "", 1, 0, 'C')
                    pdf.cell(w_l[3], 6, "X" if row['res'] == "FAIL" else "", 1, 0, 'C')
                    pdf.cell(w_l[4], 6, f" {row.get('com','')}", 1, 1, 'L')
                cnt += 1

        # 4. Summary & Issues
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, "3.0    SUMMARY & ISSUES", 0, 1)
        pdf.set_font('Arial', 'B', 9); pdf.set_fill_color(230, 230, 230)
        pdf.cell(15, 10, "NO", 1, 0, 'C', 1); pdf.cell(85, 10, "SUMMARY / ISSUES", 1, 0, 'C', 1); pdf.cell(90, 10, "REMARKS", 1, 1, 'C', 1)
        pdf.set_font('Arial', '', 8)
        for idx, item in enumerate(st.session_state['issue_list']):
            pdf.cell(15, 10, str(idx+1), 1, 0, 'C'); pdf.cell(85, 10, item['issue'], 1, 0, 'L'); pdf.cell(90, 10, item['Remarks'], 1, 1, 'L')

        # 5. Approval & Acceptance
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "4.0    APPROVAL & ACCEPTANCE", 0, 1)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, "Confirmation Statement:", 0, 1)
        
        pdf.set_font('Arial', '', 10)
        stmt = "The undersigned hereby confirms that the works described in this report have been carried out in accordance with the agreed scope, specifications, and requirements. All findings and remarks have been documented and verified accordingly."
        pdf.multi_cell(0, 6, stmt, 0, 'L')
        
        # Simpan imej sementara
        p_img.save("p.png")
        v_img.save("v.png")

        # Tentukan posisi Y untuk tanda tangan
        y_sig_start = pdf.get_y() + 10 
        
        # 1. Letak tanda tangan
        pdf.image("p.png", x=40, y=y_sig_start, w=40)
        pdf.image("v.png", x=130, y=y_sig_start, w=40)
        
        # 2. Letak teks nama dan timestamp di bawah tanda tangan
        pdf.set_y(y_sig_start + 25) 
        
        # Ambil masa semasa untuk UTC
        utc_now = datetime.now(timezone.utc)
        # Tambah 8 jam untuk Waktu Malaysia (MYT)
        myt_now = utc_now + timedelta(hours=8)
        gen_timestamp = myt_now.strftime("%d/%m/%Y %H:%M:%S")
        
        # --- Baris Nama ---
        pdf.set_font('Arial', 'B', 10)
        pdf.set_x(15)
        pdf.cell(90, 8, f"PREPARED BY: {tech_name}", 0, 0, 'C') 
        pdf.set_x(105)
        pdf.cell(90, 8, f"VERIFIED BY: {client_name}", 0, 1, 'C')

        # --- Baris Timestamp (Font lebih kecil dan Italic) ---
        pdf.set_font('Arial', 'I', 8)
        pdf.set_x(15)
        pdf.cell(90, 5, f"Date/Time (MYT): {gen_timestamp}", 0, 0, 'C')
        pdf.set_x(105)
        pdf.cell(90, 5, f"Date/Time (MYT): {gen_timestamp}", 0, 1, 'C')

        # Cleanup
        if os.path.exists("p.png"): os.remove("p.png")
        if os.path.exists("v.png"): os.remove("v.png")

        # --- 6.0 ATTACHMENTS (FORMAT JADUAL BERSEMPADAN) ---
        if evidence_data:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "5.0    ATTACHMENTS", 0, 1)
            pdf.ln(5)
            
            # --- TETAPAN AUTOMATIK (A4 = 210mm lebar) ---
            box_w = 90               # 1. Tentukan lebar kotak yang anda mahu
            box_h = 100               # 2. Tentukan tinggi kotak yang anda mahu
            gap = 5                 # 3. Jarak (gap) antara kotak kiri dan kanan
            
            # Kira margin supaya center: (Lebar Kertas - (2 kotak + 1 gap)) / 2
            margin_x = (210 - (2 * box_w + gap)) / 2
            
            col_x = [margin_x, margin_x + box_w + gap] # Koordinat X automatik
            row_y = [35, 35 + box_h + 5]              # Koordinat Y (baris 1 & 2)
            
            for i, ev in enumerate(evidence_data):
                # Tambah muka surat baru selepas setiap 4 keping gambar
                if i > 0 and i % 4 == 0:
                    pdf.add_page()
                
                pos = i % 4
                x, y = col_x[pos % 2], row_y[pos // 2]
                
                # 1. LUKIS BORDER KOTAK (Jadual)
                pdf.set_draw_color(0, 0, 0)
                pdf.set_line_width(0.3)
                pdf.rect(x, y, box_w, box_h)
                
                # 2. MASUKKAN GAMBAR
                processed_img = process_image(ev['file'])
                if processed_img:
                    temp_ev = f"tmp_ev_{i}.jpg"
                    processed_img.save(temp_ev, "JPEG", quality=95)
                    
                    # Gambar diletakkan di dalam kotak dengan padding sedikit
                    # Saiz gambar dikecilkan sedikit (85x65) supaya muat ruang teks di bawah
                    pdf.image(temp_ev, x=x+3.75, y=y+5, w=85, h=65)
                    
                    # 3. GARISAN PEMISAH (Antara Gambar & Kapsyen)
                    pdf.line(x, y + 90, x + box_w, y + 90)
                    
                    # 4. TAJUK/KAPSYEN DI BAWAH GAMBAR
                    pdf.set_xy(x, y + 90)
                    pdf.set_font('Arial', '', 10)
                    # Multi_cell supaya teks panjang automatik ke baris baru dalam kotak
                    pdf.multi_cell(box_w, 7, ev['label'], 0, 'C')
                    
                    if os.path.exists(temp_ev): 
                        os.remove(temp_ev)

        # --- LANGKAH 7: FINAL DOWNLOAD HANDLING ---
        pdf_output = pdf.output(dest='S')
        
        # Selesaikan masalah bytearray vs string
        if isinstance(pdf_output, str):
            final_bytes = pdf_output.encode('latin-1')
        else:
            final_bytes = bytes(pdf_output)

        # Membersihkan nama fail (tukar ruang kosong kepada underscore)
        clean_filename = selected_template.replace(" ", "_")
        date_str = datetime.now().strftime('%d%m%Y')

        st.download_button(
            label="📥 DOWNLOAD REPORT",
            data=final_bytes,
            # Sekarang nama fail akan jadi cth: MET_REPORT_03022026.pdf
            file_name=f"{clean_filename}_{date_str}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

