import streamlit as st
from fpdf import FPDF
import os
import json
import base64
import tempfile
from datetime import datetime, timedelta, timezone, date
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# =========================================================
# 1. PAGE CONFIG
# =========================================================
st.set_page_config(page_title="VTMS Reporting System", layout="wide")

# =========================================================
# 2. TEMPLATE FILES
# =========================================================
TEMPLATE_FILE = "templates.json"
TAMBAHAN_FILE = "templates_tambahan.json"  # simpanan perubahan user


def get_default_templates():
    return {
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
                ["SERVER TASKS", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", "Restart services or applications if necessary"]],
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
                ["SERVER TASKS", ["Equipment operate without alarm", "Check system health and hardware status (CPU, RAM, disk usage)", "Check application and system logs for errors", "Check Windows update", "Verify archived data make sure 3 month previous data available", "Restart services or applications if necessary"]],
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


def load_templates():
    defaults = get_default_templates()

    if not os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            json.dump(defaults, f, indent=4, ensure_ascii=False)

    if os.path.exists(TAMBAHAN_FILE):
        try:
            with open(TAMBAHAN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return defaults

    return defaults


def save_templates_to_file():
    with open(TAMBAHAN_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["all_templates"], f, indent=4, ensure_ascii=False)


# =========================================================
# 3. SESSION INIT
# =========================================================
if "all_templates" not in st.session_state:
    st.session_state["all_templates"] = load_templates()

if "issue_list" not in st.session_state:
    st.session_state["issue_list"] = []


# =========================================================
# 4. S/N DATABASE
# =========================================================
sn_database = {
    "Check SN :": [
        "4CE442B8B8", "4CE442B8B7", "4CE442B8BD",
        "4CE442B8BB", "4CE442B8BC", "4CE442B8B9",
        "UI01245140306", "UI01245140305", "UI01245140309",
        "VHF-A-9921", "VHF-A-9922",
        "VHF-B-8831", "VHF-B-8832"
    ],
    "Check ID(*localhost 127.0.0.1 1947) :": [
        "1563220541", "75770141", "689509092",
        "1151380960", "2048014076", "338176953"
    ],
    "Monitor 1 Check SN :": [
        "CNC4431M34", "CNC4431M33", "CNC4431M32",
        "CNC4431M39", "CNC4431M36", "CNC4431M38"
    ],
    "Monitor 2 Check SN :": [
        "CNC4431M34", "CNC4431M33", "CNC4431M32",
        "CNC4431M39", "CNC4431M36", "CNC4431M38"
    ],
    "Check ID (Note in Remark)": [
        "AW121390192", "AW122210344", "AW119430008"
    ],
    "Check SN:": [
        "AW121390192", "AW122210344", "AW119430008"
    ]
}


# =========================================================
# 5. IMAGE / SIGNATURE HELPERS
# =========================================================
def process_image(img_input, target_size=(800, 600)):
    if img_input is None:
        return None
    try:
        img = Image.open(img_input).convert("RGBA")
        background = Image.new("RGB", target_size, (255, 255, 255))
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        background.paste(img, offset, mask=img.getchannel("A"))
        return background
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None


def process_signature(img_input):
    if img_input is None:
        return None

    try:
        arr = img_input.astype("uint8")

        if len(arr.shape) != 3 or arr.shape[2] != 4:
            return None

        img = Image.fromarray(arr, "RGBA")
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()

        if not bbox:
            return None

        img = img.crop(bbox)
        alpha_cropped = img.getchannel("A")

        new_img = Image.new("RGB", img.size, (255, 255, 255))
        new_img.paste(img, mask=alpha_cropped)
        return new_img
    except Exception:
        return None


def process_uploaded_signature(uploaded_file, target_size=(600, 200)):
    if uploaded_file is None:
        return None

    try:
        img = Image.open(uploaded_file).convert("RGBA")

        # crop ikut content jika ada transparency
        try:
            alpha = img.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                img = img.crop(bbox)
        except Exception:
            pass

        background = Image.new("RGB", target_size, (255, 255, 255))
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        background.paste(img, offset, mask=img.getchannel("A"))
        return background
    except Exception as e:
        st.error(f"Error processing uploaded signature: {e}")
        return None


def get_signature_image(uploaded_file, canvas_image_data):
    # priority: upload image > canvas drawing
    uploaded_sig = process_uploaded_signature(uploaded_file)
    if uploaded_sig is not None:
        return uploaded_sig
    return process_signature(canvas_image_data)


def pdf_split_lines(pdf_obj, width, text):
    text = "" if text is None else str(text)
    try:
        lines = pdf_obj.multi_cell(width, 5, text, split_only=True)
        return lines if lines else [""]
    except TypeError:
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


# =========================================================
# 6. PDF CLASS
# =========================================================
class VTMS_Full_Report(FPDF):
    def __init__(self, header_title=""):
        super().__init__()
        self.header_title = header_title
        self.set_auto_page_break(auto=False)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(100)
            self.cell(0, 5, self.header_title, 0, 1, "R")
            self.line(10, 15, 200, 15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(0)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def cover_page(self, data, logo_path=None):
        self.add_page()
        self.rect(5, 5, 200, 287)

        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, x=75, y=20, w=60)

        self.set_font("Arial", "B", 12)
        self.ln(65)
        self.cell(0, 5, "SYSTEM OWNER", 0, 1, "C")

        self.set_font("Arial", "B", 16)
        self.multi_cell(0, 8, data["owner"].upper(), 0, "C")
        self.ln(10)

        self.set_font("Arial", "B", 10)
        self.cell(0, 5, "PROJECT REFERENCE NO:", 0, 1, "C")

        self.set_font("Arial", "", 10)
        self.multi_cell(0, 5, data["ref"], 0, "C")
        self.ln(25)

        self.set_font("Arial", "B", 18)
        self.cell(0, 10, "DOCUMENT TITLE:", 0, 1, "C")

        self.set_font("Arial", "B", 22)
        self.multi_cell(0, 12, data["title"].upper(), 0, "C")
        self.ln(35)

        for k, v in [("LOCATION", data["loc"]), ("DOCUMENT ID", data["id"]), ("DATE", data["dt"])]:
            self.set_x(35)
            self.set_font("Arial", "B", 11)
            self.cell(50, 12, k, 1, 0, "L")
            self.set_font("Arial", "", 11)
            self.cell(90, 12, v, 1, 1, "L")


# =========================================================
# 7. SIDEBAR
# =========================================================
with st.sidebar:
    FIXED_LOGO_PATH = "logo.png"

    if os.path.exists(FIXED_LOGO_PATH):
        st.image(FIXED_LOGO_PATH, caption="Current Company Logo", width=150)
    else:
        st.warning(f"Fail {FIXED_LOGO_PATH} tidak dijumpai dalam folder. Report masih boleh dijana tanpa logo.")

    with st.expander("✨ CREATE NEW TEMPLATE"):
        n_name = st.text_input("Template Name")
        n_type = st.radio("Format", ["checkbox", "technical"])
        if st.button("Build Template"):
            if n_name.strip():
                h_l = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"] if n_type == "checkbox" else ["NO", "ITEM", "SPEC", "ACTUAL", "RESULT"]
                w_l = [10, 110, 15, 15, 40] if n_type == "checkbox" else [10, 75, 40, 40, 25]
                st.session_state["all_templates"][n_name.strip()] = {
                    "headers": h_l,
                    "widths": w_l,
                    "type": n_type,
                    "content": [["1.0 DETAILS", ["First Item"]]]
                }
                save_templates_to_file()
                st.rerun()

    st.divider()
    selected_template = st.selectbox("Template Type:", list(st.session_state["all_templates"].keys()))

    with st.expander("📝 EDIT SECTION / TASKS"):
        st.subheader("Manage Sections")
        new_sec = st.text_input("New Section Name")

        col1, col2 = st.columns(2)
        if col1.button("➕ Add Section"):
            if new_sec.strip():
                st.session_state["all_templates"][selected_template]["content"].append([new_sec.strip(), ["New Item"]])
                save_templates_to_file()
                st.rerun()

        sec_names = [s[0] for s in st.session_state["all_templates"][selected_template]["content"]]
        target_sec_del = st.selectbox("Select Section to Delete", sec_names)

        if col2.button("🗑️ Delete Section", type="secondary"):
            st.session_state["all_templates"][selected_template]["content"] = [
                s for s in st.session_state["all_templates"][selected_template]["content"]
                if s[0] != target_sec_del
            ]
            save_templates_to_file()
            st.rerun()

        st.divider()
        st.subheader("Manage Tasks")

        target_sec = st.selectbox("Select Target Section", sec_names)

        current_tasks = []
        for s in st.session_state["all_templates"][selected_template]["content"]:
            if s[0] == target_sec:
                current_tasks = s[1]
                break

        new_t_name = st.text_input("New Task Name")
        col3, col4 = st.columns(2)

        if col3.button("➕ Add Task"):
            if new_t_name.strip():
                for item in st.session_state["all_templates"][selected_template]["content"]:
                    if item[0] == target_sec:
                        item[1].append(new_t_name.strip())
                        break
                save_templates_to_file()
                st.rerun()

        if current_tasks:
            target_task_del = st.selectbox("Select Task to Delete", current_tasks)
            if col4.button("🗑️ Delete Task"):
                for item in st.session_state["all_templates"][selected_template]["content"]:
                    if item[0] == target_sec and target_task_del in item[1]:
                        item[1].remove(target_task_del)
                        break
                save_templates_to_file()
                st.rerun()

    if st.button("♻️ Reset to Original Template", type="secondary"):
        if os.path.exists(TAMBAHAN_FILE):
            os.remove(TAMBAHAN_FILE)
        st.session_state["all_templates"] = get_default_templates()
        st.rerun()

    st.divider()
    sys_owner = st.text_area("System Owner", "LEMBAGA PELABUHAN JOHOR")
    proj_ref = st.text_area("Project Reference", "JPA/IP/PA(S)01-222\n'VESSEL TRAFFIC MANAGEMENT SYSTEM (VTMS)'")
    header_txt = st.text_input("Header Title", "VTMS REPORT - JPA/IP/PA(S)01-222")
    doc_id = st.text_input("Document ID", "LPJPTP/VTMS/2026")
    loc = st.text_input("Location", "VTS TOWER, TANJUNG PELEPAS")
    tech_name = st.text_input("Team Details", "Daus Works")
    client_name = st.text_input("Client Name", "NAZAME")
    report_dt = st.date_input("Date", date.today()).strftime("%d/%m/%Y")


# =========================================================
# 8. CHECKLIST RENDER
# =========================================================
config = st.session_state["all_templates"][selected_template]
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
                checklist_results.append({
                    "task": t,
                    "res": res,
                    "spec": spec,
                    "actual": act
                })
            else:
                c1, c3 = st.columns([1, 2])
                res = c1.radio(t, ["PASS", "FAIL", "N/A"], key=f"rad_{u_key}", horizontal=True)

                if t.strip() in sn_database:
                    selected_value = c3.selectbox(
                        "Select SN / ID",
                        ["Manual Input"] + sn_database[t.strip()],
                        key=f"sel_{u_key}"
                    )
                    rem = c3.text_input("Input SN / ID", key=f"inp_{u_key}") if selected_value == "Manual Input" else selected_value
                else:
                    rem = c3.text_input("Remarks", key=f"rem_{u_key}")

                checklist_results.append({
                    "task": t,
                    "res": res,
                    "com": rem
                })


# =========================================================
# 9. SUMMARY & ISSUES
# =========================================================
st.divider()
st.header("⚠️ SUMMARY & ISSUES")

for i, item in enumerate(st.session_state["issue_list"]):
    c1, c2 = st.columns(2)
    st.session_state["issue_list"][i]["issue"] = c1.text_area(f"Issue {i+1}", item["issue"], key=f"is_{i}")
    st.session_state["issue_list"][i]["Remarks"] = c2.text_area(f"Remarks {i+1}", item["Remarks"], key=f"ac_{i}")

if st.button("➕ Add Issue"):
    st.session_state["issue_list"].append({"issue": "", "Remarks": ""})
    st.rerun()


# =========================================================
# 10. EVIDENCE
# =========================================================
st.divider()
st.header("🖼️ EVIDENCE")

u_files = st.file_uploader("Upload Evidence", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
evidence_data = []

if u_files:
    cols = st.columns(4)
    for idx, f in enumerate(u_files):
        with cols[idx % 4]:
            st.image(f, use_container_width=True)
            cap = st.text_input(f"Caption {idx+1}", f"Evidence {idx+1}", key=f"cap_{idx}")
            evidence_data.append({"file": f, "label": cap})


# =========================================================
# 11. SIGNATURES
# =========================================================
st.divider()
st.header("✍️ APPROVAL")

ca, cb = st.columns(2)

with ca:
    st.write("Prepared By:")
    prepared_sig_upload = st.file_uploader(
        "Upload Prepared By Signature",
        type=["png", "jpg", "jpeg"],
        key="prepared_sig_upload"
    )
    if prepared_sig_upload:
        st.image(prepared_sig_upload, width=250)
    st.caption("Atau sign guna ruangan bawah")
    sig1 = st_canvas(
        stroke_width=2,
        height=150,
        width=300,
        key="sig1",
        background_color="#ffffff"
    )

with cb:
    st.write("Verified By:")
    verified_sig_upload = st.file_uploader(
        "Upload Verified By Signature",
        type=["png", "jpg", "jpeg"],
        key="verified_sig_upload"
    )
    if verified_sig_upload:
        st.image(verified_sig_upload, width=250)
    st.caption("Atau sign guna ruangan bawah")
    sig2 = st_canvas(
        stroke_width=2,
        height=150,
        width=300,
        key="sig2",
        background_color="#ffffff"
    )


# =========================================================
# 12. PDF GENERATION
# =========================================================
if st.button("🚀 GENERATE FINAL REPORT", type="primary", use_container_width=True):
    p_img = get_signature_image(prepared_sig_upload, sig1.image_data)
    v_img = get_signature_image(verified_sig_upload, sig2.image_data)

    if p_img is None or v_img is None:
        st.error("Sila upload signature image atau turunkan tanda tangan terlebih dahulu untuk kedua-dua ruangan!")
    else:
        pdf = VTMS_Full_Report(header_title=header_txt)
        logo_to_use = FIXED_LOGO_PATH if os.path.exists(FIXED_LOGO_PATH) else None

        # Cover
        pdf.cover_page({
            "owner": sys_owner,
            "ref": proj_ref,
            "title": selected_template,
            "loc": loc,
            "id": doc_id,
            "dt": report_dt
        }, logo_path=logo_to_use)

        # TOC
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "TABLE OF CONTENTS", 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", "", 11)
        toc_items = [
            ("2.0", "DETAILS / CHECKLIST"),
            ("3.0", "SUMMARY & ISSUES"),
            ("4.0", "APPROVAL"),
            ("5.0", "ATTACHMENTS")
        ]
        for n, t in toc_items:
            pdf.cell(10, 10, n, 0, 0)
            pdf.cell(0, 10, t, 0, 1)

        # Checklist
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "2.0    DETAILS / CHECKLIST", 0, 1)

        h_l, w_l = config["headers"], config["widths"]
        pdf.set_font("Arial", "B", 8)
        pdf.set_fill_color(230, 230, 230)

        for i, h in enumerate(h_l):
            pdf.cell(w_l[i], 8, h, 1, 0, "C", 1)
        pdf.ln()

        cnt = 1
        for row in checklist_results:
            if row["res"] == "TITLE":
                pdf.set_font("Arial", "B", 8)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(sum(w_l), 8, f" {row['task']}", 1, 1, "L", 1)
                cnt = 1
            else:
                pdf.set_font("Arial", "", 7)

                if config.get("type") == "technical":
                    row_h = 8
                else:
                    txt_remark = str(row.get("com", ""))
                    lines = pdf_split_lines(pdf, w_l[4], txt_remark)
                    line_count = len(lines)
                    row_h = max(8, line_count * 5)

                if pdf.get_y() + row_h > 270:
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 8)
                    pdf.set_fill_color(230, 230, 230)
                    for i, h in enumerate(h_l):
                        pdf.cell(w_l[i], 8, h, 1, 0, "C", 1)
                    pdf.ln()
                    pdf.set_font("Arial", "", 7)

                curr_x = pdf.get_x()
                curr_y = pdf.get_y()

                pdf.cell(w_l[0], row_h, str(cnt), 1, 0, "C")
                pdf.cell(w_l[1], row_h, f" {row['task']}", 1, 0, "L")

                if config.get("type") == "technical":
                    pdf.cell(w_l[2], row_h, row.get("spec", "-"), 1, 0, "C")
                    pdf.cell(w_l[3], row_h, row.get("actual", "-"), 1, 0, "C")
                    pdf.cell(w_l[4], row_h, row["res"], 1, 0, "C")
                else:
                    pdf.cell(w_l[2], row_h, "X" if row["res"] == "PASS" else "", 1, 0, "C")
                    pdf.cell(w_l[3], row_h, "X" if row["res"] == "FAIL" else "", 1, 0, "C")

                    remark_x = curr_x + w_l[0] + w_l[1] + w_l[2] + w_l[3]
                    txt_remark = str(row.get("com", ""))
                    lines = pdf_split_lines(pdf, w_l[4], txt_remark)
                    line_count = len(lines)

                    pdf.set_xy(remark_x, curr_y)
                    pdf.cell(w_l[4], row_h, "", 1, 0)

                    text_y = curr_y + max(0, (row_h - (line_count * 5)) / 2)
                    pdf.set_xy(remark_x, text_y)
                    pdf.multi_cell(w_l[4], 5, txt_remark, 0, "L")

                pdf.set_xy(curr_x, curr_y + row_h)
                cnt += 1

        # Summary & Issues
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "3.0    SUMMARY & ISSUES", 0, 1)

        w_issue = [15, 85, 90]

        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(w_issue[0], 10, "NO", 1, 0, "C", 1)
        pdf.cell(w_issue[1], 10, "SUMMARY / ISSUES", 1, 0, "C", 1)
        pdf.cell(w_issue[2], 10, "REMARKS", 1, 1, "C", 1)

        pdf.set_font("Arial", "", 8)

        for idx, item in enumerate(st.session_state["issue_list"]):
            txt_issue = str(item["issue"])
            txt_remark = str(item["Remarks"])

            lines_issue = pdf_split_lines(pdf, w_issue[1], txt_issue)
            lines_remark = pdf_split_lines(pdf, w_issue[2], txt_remark)

            max_lines = max(len(lines_issue), len(lines_remark))
            row_h = max(10, max_lines * 5)

            if pdf.get_y() + row_h > 270:
                pdf.add_page()
                pdf.set_font("Arial", "B", 9)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(w_issue[0], 10, "NO", 1, 0, "C", 1)
                pdf.cell(w_issue[1], 10, "SUMMARY / ISSUES", 1, 0, "C", 1)
                pdf.cell(w_issue[2], 10, "REMARKS", 1, 1, "C", 1)
                pdf.set_font("Arial", "", 8)

            curr_x = pdf.get_x()
            curr_y = pdf.get_y()

            pdf.cell(w_issue[0], row_h, str(idx + 1), 1, 0, "C")

            pdf.cell(w_issue[1], row_h, "", 1, 0)
            pdf.set_xy(curr_x + w_issue[0], curr_y + max(0, (row_h - len(lines_issue) * 5) / 2))
            pdf.multi_cell(w_issue[1], 5, txt_issue, 0, "L")

            pdf.set_xy(curr_x + w_issue[0] + w_issue[1], curr_y)
            pdf.cell(w_issue[2], row_h, "", 1, 0)
            pdf.set_xy(curr_x + w_issue[0] + w_issue[1], curr_y + max(0, (row_h - len(lines_remark) * 5) / 2))
            pdf.multi_cell(w_issue[2], 5, txt_remark, 0, "L")

            pdf.set_xy(curr_x, curr_y + row_h)

        # Approval
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "4.0    APPROVAL & ACCEPTANCE", 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", "", 10)
        stmt = "The undersigned hereby confirms that the works described in this report have been carried out in accordance with agreed scope."
        pdf.multi_cell(0, 6, stmt, 0, "L")

        temp_files_to_delete = []

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_p:
                p_img.save(tmp_p.name)
                p_path = tmp_p.name
                temp_files_to_delete.append(p_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_v:
                v_img.save(tmp_v.name)
                v_path = tmp_v.name
                temp_files_to_delete.append(v_path)

            y_sig = pdf.get_y() + 10
            pdf.image(p_path, x=40, y=y_sig, w=40)
            pdf.image(v_path, x=130, y=y_sig, w=40)

            pdf.set_y(y_sig + 25)

            myt_now = datetime.now(timezone.utc) + timedelta(hours=8)
            gen_timestamp = myt_now.strftime("%d/%m/%Y %H:%M:%S")

            pdf.set_font("Arial", "B", 10)
            pdf.set_x(15)
            pdf.cell(90, 8, f"PREPARED BY: {tech_name}", 0, 0, "C")
            pdf.set_x(105)
            pdf.cell(90, 8, f"VERIFIED BY: {client_name}", 0, 1, "C")

            pdf.set_font("Arial", "I", 8)
            pdf.set_x(15)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 0, "C")
            pdf.set_x(105)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 1, "C")

            # Attachments
            if evidence_data:
                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "5.0    ATTACHMENTS", 0, 1)
                pdf.ln(5)

                if "SERVER REPORT" in selected_template:
                    for i, ev in enumerate(evidence_data):
                        if i > 0 and i % 2 == 0:
                            pdf.add_page()

                        pos_in_page = i % 2
                        x = 30
                        y = 35 if pos_in_page == 0 else 145

                        processed_img = process_image(ev["file"])
                        if processed_img:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_ev:
                                processed_img.save(tmp_ev.name, "JPEG")
                                tmp_path = tmp_ev.name
                                temp_files_to_delete.append(tmp_path)

                            pdf.rect(x, y, 150, 100)
                            pdf.image(tmp_path, x=x + 2, y=y + 2, w=145, h=90)

                            pdf.set_xy(x, y + 95)
                            pdf.set_font("Arial", "B", 10)
                            pdf.multi_cell(150, 6, ev["label"], 0, "C")
                else:
                    for i, ev in enumerate(evidence_data):
                        if i > 0 and i % 4 == 0:
                            pdf.add_page()

                        pos = i % 4
                        x = [20, 110][pos % 2]
                        y = [40, 145][pos // 2]

                        processed_img = process_image(ev["file"])
                        if processed_img:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_ev:
                                processed_img.save(tmp_ev.name, "JPEG")
                                tmp_path = tmp_ev.name
                                temp_files_to_delete.append(tmp_path)

                            pdf.rect(x, y, 80, 80)
                            pdf.image(tmp_path, x=x + 2, y=y + 2, w=76, h=60)

                            pdf.set_xy(x, y + 65)
                            pdf.set_font("Arial", "", 9)
                            pdf.multi_cell(80, 5, ev["label"], 0, "C")

            pdf_output = pdf.output(dest="S")
            final_bytes = pdf_output.encode("latin-1") if isinstance(pdf_output, str) else bytes(pdf_output)

            date_str = myt_now.strftime("%d%m%Y")
            clean_filename = selected_template.replace(" ", "_")
            full_file_name = f"{clean_filename}_{date_str}.pdf"

            st.divider()

            b64 = base64.b64encode(final_bytes).decode("utf-8")
            new_tab_js = f"""
                <script>
                    function openPDF() {{
                        var pdfData = "data:application/pdf;base64,{b64}";
                        var win = window.open();
                        win.document.write('<iframe src="' + pdfData + '" frameborder="0" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;" allowfullscreen></iframe>');
                    }}
                </script>
                <button onclick="openPDF()" style="width:100%; background-color:#2e7bcf; color:white; padding:12px; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">
                    👁️ PREVIEW REPORT IN NEW TAB
                </button>
            """
            st.components.v1.html(new_tab_js, height=60)

            st.download_button(
                label=f"📥 DOWNLOAD {full_file_name}",
                data=final_bytes,
                file_name=full_file_name,
                mime="application/pdf",
                use_container_width=True
            )

        finally:
            for file_path in temp_files_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
