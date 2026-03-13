import streamlit as st
from fpdf import FPDF
import os
import json
import base64
import tempfile
from datetime import datetime, timedelta, timezone, date
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import copy

# =========================================================
# 1. PAGE CONFIG
# =========================================================
st.set_page_config(page_title="VTMS Reporting System", layout="wide")

# =========================================================
# 2. FILES
# =========================================================
MAINT_TEMPLATE_FILE = "maintenance_templates.json"

# =========================================================
# 3. DEFAULT DATA
# =========================================================
DEFAULT_MAINTENANCE_SECTIONS = [
    {
        "title": "1.0 PHYSICAL INSPECTION",
        "tasks": [
            "No physical defect",
            "Equipment condition satisfactory",
            "Cable / connector inspection",
            "Housekeeping"
        ]
    },
    {
        "title": "2.0 POWER / HARDWARE CHECK",
        "tasks": [
            "Power status normal",
            "Indicator / alarm status normal",
            "Check hardware condition",
            "Check grounding / protection"
        ]
    },
    {
        "title": "3.0 NETWORK / COMMUNICATION CHECK",
        "tasks": [
            "Network connectivity test",
            "Communication test",
            "Data transmission / receiving test"
        ]
    },
    {
        "title": "4.0 SOFTWARE / SYSTEM CHECK",
        "tasks": [
            "Software functioning normally",
            "System log check",
            "Error / alarm check",
            "Backup / storage check"
        ]
    },
    {
        "title": "5.0 CORRECTIVE / REMARKS",
        "tasks": [
            "Adjustment / cleaning performed",
            "Repair / replacement required",
            "Further monitoring required"
        ]
    }
]

# =========================================================
# 4. TEMPLATE STORAGE
# =========================================================
def ensure_json_file(filepath, default_content):
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=4, ensure_ascii=False)


def load_json_file(filepath, fallback):
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return copy.deepcopy(fallback)


def save_json_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)


ensure_json_file(
    MAINT_TEMPLATE_FILE,
    {"Default Maintenance": DEFAULT_MAINTENANCE_SECTIONS}
)

if "maintenance_templates" not in st.session_state:
    st.session_state["maintenance_templates"] = load_json_file(
        MAINT_TEMPLATE_FILE,
        {"Default Maintenance": DEFAULT_MAINTENANCE_SECTIONS}
    )

if "maintenance_sections" not in st.session_state:
    st.session_state["maintenance_sections"] = copy.deepcopy(DEFAULT_MAINTENANCE_SECTIONS)

if "team_members" not in st.session_state:
    st.session_state["team_members"] = ["Daus", "Amin", "XXX"]

# =========================================================
# 5. HELPERS
# =========================================================
def process_image(img_input, target_size=(1000, 700)):
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


def process_signature(canvas_image_data):
    if canvas_image_data is None:
        return None
    try:
        arr = canvas_image_data.astype("uint8")
        if len(arr.shape) != 3 or arr.shape[2] != 4:
            return None

        img = Image.fromarray(arr, "RGBA")
        alpha = img.getchannel("A")
        bbox = alpha.getbbox()

        if not bbox:
            return None

        img = img.crop(bbox)
        alpha_cropped = img.getchannel("A")

        output = Image.new("RGB", img.size, (255, 255, 255))
        output.paste(img, mask=alpha_cropped)
        return output
    except Exception:
        return None


def process_uploaded_signature(uploaded_file, target_size=(600, 200)):
    if uploaded_file is None:
        return None
    try:
        img = Image.open(uploaded_file).convert("RGBA")
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


def draw_attachment_grid(pdf, items, temp_files_to_delete, section_title="ATTACHMENTS"):
    if not items:
        return

    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, section_title, 0, 1)
    pdf.ln(5)

    for i, item in enumerate(items):
        if i > 0 and i % 4 == 0:
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"{section_title} (CONT'D)", 0, 1)
            pdf.ln(5)

        pos = i % 4
        x = [20, 110][pos % 2]
        y = [40, 155][pos // 2]

        img_file = item.get("file") or item.get("image")
        caption = item.get("label") or item.get("caption", "")
        title = item.get("title", "")

        processed = process_image(img_file, target_size=(900, 650))
        if processed:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                processed.save(tmp.name, "JPEG")
                tmp_path = tmp.name
                temp_files_to_delete.append(tmp_path)

            pdf.rect(x, y, 80, 95)
            pdf.image(tmp_path, x=x + 2, y=y + 2, w=76, h=52)

            if title:
                pdf.set_xy(x + 3, y + 56)
                pdf.set_font("Arial", "B", 7)
                pdf.multi_cell(74, 4, title, 0, "C")

                pdf.set_xy(x + 4, y + 68)
                pdf.set_font("Arial", "", 7)
                pdf.multi_cell(72, 4, caption, 0, "C")
            else:
                pdf.set_xy(x + 4, y + 62)
                pdf.set_font("Arial", "", 8)
                pdf.multi_cell(72, 5, caption, 0, "C")


def format_team_members_list(team_members):
    cleaned = [str(x).strip() for x in team_members if str(x).strip()]
    if not cleaned:
        return "NIL"
    return "\n".join([f"{i}. {name}" for i, name in enumerate(cleaned, start=1)])


# =========================================================
# 6. PDF CLASS
# =========================================================
class ReportPDF(FPDF):
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
        st.warning("Logo tidak dijumpai. Report masih boleh dijana tanpa logo.")

    selected_template = st.selectbox(
        "Template Type",
        ["MAINTENANCE REPORT", "INSTALLATION REPORT"]
    )

    st.divider()
    sys_owner = st.text_area("System Owner", "LEMBAGA PELABUHAN JOHOR")
    proj_ref = st.text_area("Project Reference", "JPA/IP/PA(S)01-222\n'VESSEL TRAFFIC MANAGEMENT SYSTEM (VTMS)'")
    header_txt = st.text_input("Header Title", "VTMS REPORT")
    doc_id = st.text_input("Document ID", "LPJPTP/VTMS/2026")
    loc = st.text_input("Location", "VTS TOWER, TANJUNG PELEPAS")

    st.divider()
    st.subheader("Team Details")

    for idx in range(len(st.session_state["team_members"])):
        c1, c2 = st.columns([5, 1])
        st.session_state["team_members"][idx] = c1.text_input(
            f"Team Member {idx + 1}",
            value=st.session_state["team_members"][idx],
            key=f"team_member_{idx}"
        )
        if c2.button("❌", key=f"delete_team_member_{idx}"):
            st.session_state["team_members"].pop(idx)
            st.rerun()

    add_tm1, add_tm2 = st.columns([4, 1])
    new_team_member = add_tm1.text_input("New Team Member", key="new_team_member")
    if add_tm2.button("➕ Add"):
        if new_team_member.strip():
            st.session_state["team_members"].append(new_team_member.strip())
            st.rerun()

    prepared_by_name = st.text_input("Prepared By (Approver Name)", "Daus Works")
    verified_by_name = st.text_input("Verified By (Approver Name)", "Client Representative")
    report_dt = st.date_input("Date", date.today()).strftime("%d/%m/%Y")

team_details_formatted = format_team_members_list(st.session_state["team_members"])

# =========================================================
# 8. COMMON VARIABLES
# =========================================================
remarks = ""
parts_used = ""
maintenance_results = []
installation_results = []
evidence_data = []

equipment_name = ""
maintenance_type = ""

customer_name = ""
customer_address = ""
onsite_team = ""
start_time = ""
end_time = ""
category = ""
service = ""
problem = ""

# =========================================================
# 9. MAINTENANCE REPORT UI
# =========================================================
if selected_template == "MAINTENANCE REPORT":
    st.header("📋 MAINTENANCE REPORT")

    c1, c2 = st.columns(2)
    equipment_name = c1.text_input("Equipment / System Name", "")
    maintenance_type = c2.text_input("Maintenance Type", "Preventive Maintenance")

    st.divider()
    st.subheader("Team Details Preview")
    st.text(team_details_formatted)

    st.divider()
    st.subheader("Maintenance Template Manager")

    ctm1, ctm2, ctm3 = st.columns([2, 1, 1])
    selected_maint_template = ctm1.selectbox(
        "Load Maintenance Template",
        list(st.session_state["maintenance_templates"].keys()),
        key="selected_maint_template"
    )

    if ctm2.button("📂 Load Template"):
        st.session_state["maintenance_sections"] = copy.deepcopy(
            st.session_state["maintenance_templates"][selected_maint_template]
        )
        st.rerun()

    if ctm3.button("♻️ Reset Default"):
        st.session_state["maintenance_sections"] = copy.deepcopy(DEFAULT_MAINTENANCE_SECTIONS)
        st.rerun()

    ctm4, ctm5 = st.columns([3, 1])
    new_maint_template_name = ctm4.text_input("Save As Template Name", key="new_maint_template_name")
    if ctm5.button("💾 Save Template"):
        if new_maint_template_name.strip():
            st.session_state["maintenance_templates"][new_maint_template_name.strip()] = copy.deepcopy(
                st.session_state["maintenance_sections"]
            )
            save_json_file(MAINT_TEMPLATE_FILE, st.session_state["maintenance_templates"])
            st.success("Maintenance template saved.")

    delete_mt_col1, delete_mt_col2 = st.columns([3, 1])
    delete_maint_template_name = delete_mt_col1.selectbox(
        "Delete Maintenance Template",
        list(st.session_state["maintenance_templates"].keys()),
        key="delete_maint_template_name"
    )
    if delete_mt_col2.button("🗑️ Delete Template"):
        if delete_maint_template_name != "Default Maintenance":
            del st.session_state["maintenance_templates"][delete_maint_template_name]
            save_json_file(MAINT_TEMPLATE_FILE, st.session_state["maintenance_templates"])
            st.success("Maintenance template deleted.")
            st.rerun()
        else:
            st.warning("Default Maintenance tidak boleh dipadam.")

    st.divider()
    st.subheader("Checklist Template Editor")

    add_sec_col1, add_sec_col2 = st.columns([2, 1])
    new_section_name = add_sec_col1.text_input("New Section Name", key="new_maintenance_section")
    if add_sec_col2.button("➕ Add Section"):
        if new_section_name.strip():
            st.session_state["maintenance_sections"].append({
                "title": new_section_name.strip(),
                "tasks": ["New Task"]
            })
            st.rerun()

    st.divider()

    for sec_idx, sec in enumerate(st.session_state["maintenance_sections"]):
        with st.expander(f"Section {sec_idx+1}", expanded=True):
            title_col1, title_col2 = st.columns([4, 1])

            sec["title"] = title_col1.text_input(
                "Section Title",
                value=sec["title"],
                key=f"sec_title_{sec_idx}"
            )

            if title_col2.button("🗑️ Delete Section", key=f"del_sec_{sec_idx}"):
                st.session_state["maintenance_sections"].pop(sec_idx)
                st.rerun()

            st.markdown("**Tasks**")

            for task_idx, task in enumerate(sec["tasks"]):
                tcol1, tcol2 = st.columns([5, 1])
                sec["tasks"][task_idx] = tcol1.text_input(
                    f"Task {task_idx+1}",
                    value=task,
                    key=f"task_{sec_idx}_{task_idx}"
                )
                if tcol2.button("❌", key=f"del_task_{sec_idx}_{task_idx}"):
                    st.session_state["maintenance_sections"][sec_idx]["tasks"].pop(task_idx)
                    st.rerun()

            add_task_col1, add_task_col2 = st.columns([4, 1])
            new_task = add_task_col1.text_input("New Task", key=f"new_task_{sec_idx}")
            if add_task_col2.button("➕ Add Task", key=f"add_task_{sec_idx}"):
                if new_task.strip():
                    st.session_state["maintenance_sections"][sec_idx]["tasks"].append(new_task.strip())
                    st.rerun()

    st.divider()
    st.subheader("Maintenance Checklist")

    headers = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"]
    widths = [10, 110, 15, 15, 40]

    for sec_idx, sec in enumerate(st.session_state["maintenance_sections"]):
        maintenance_results.append({"task": sec["title"], "res": "TITLE", "com": ""})
        with st.expander(sec["title"], expanded=True):
            for task_idx, task in enumerate(sec["tasks"]):
                c1, c2 = st.columns([1, 2])
                res = c1.radio(
                    task,
                    ["PASS", "FAIL", "N/A"],
                    key=f"rad_{sec_idx}_{task_idx}",
                    horizontal=True
                )
                rem = c2.text_input("Remarks", key=f"rem_{sec_idx}_{task_idx}")
                maintenance_results.append({
                    "task": task,
                    "res": res,
                    "com": rem
                })

    st.divider()
    remarks = st.text_area("Maintenance Summary / Remarks", height=120)

    st.divider()
    st.subheader("Evidence")
    u_files = st.file_uploader(
        "Upload Evidence",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
        key="maintenance_evidence"
    )

    if u_files:
        cols = st.columns(4)
        for idx, f in enumerate(u_files):
            with cols[idx % 4]:
                st.image(f, use_container_width=True)
                cap = st.text_input(f"Caption {idx+1}", f"Evidence {idx+1}", key=f"mcap_{idx}")
                evidence_data.append({"file": f, "label": cap})

# =========================================================
# 10. INSTALLATION REPORT UI
# =========================================================
if selected_template == "INSTALLATION REPORT":
    st.header("📋 INSTALLATION REPORT")

    st.subheader("Site Information")
    c1, c2 = st.columns(2)

    with c1:
        customer_name = st.text_input("Customer Name", "Telekom Malaysia")
        customer_address = st.text_area("Customer Address", "TM Pengerang")
        onsite_team = st.text_input("Onsite Team / Lead", "Daus Works Team")

    with c2:
        start_time = st.text_input("On Site Start Time", "08:30")
        end_time = st.text_input("Completed Time", "16:30")
        category = st.text_input("Category", "Installation")
        service = st.text_input("Service", "Equipment Installation")
        problem = st.text_input("Problem / Scope", "New installation and commissioning")

    st.divider()
    st.subheader("Team Details Preview")
    st.text(team_details_formatted)

    st.divider()
    remarks = st.text_area("Work Description / Remarks", height=120)

    st.divider()
    st.subheader("Installation Photos (Dynamic)")

    inst_files = st.file_uploader(
        "Upload Installation Photo(s)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="dynamic_installation_photos"
    )

    if inst_files:
        for idx, file in enumerate(inst_files):
            st.markdown(f"### Photo {idx + 1}")
            c1, c2 = st.columns([1, 1])

            with c1:
                st.image(file, use_container_width=True)

            with c2:
                sec_title = st.text_input(
                    f"Section Title for Photo {idx + 1}",
                    value=f"{idx + 3}.0 INSTALLATION PHOTO {idx + 1}",
                    key=f"dyn_inst_title_{idx}"
                )
                caption = st.text_area(
                    f"Caption for Photo {idx + 1}",
                    value=f"Installation photo {idx + 1}",
                    key=f"dyn_inst_caption_{idx}",
                    height=100
                )

            installation_results.append({
                "title": sec_title,
                "image": file,
                "caption": caption
            })

    st.divider()
    parts_used = st.text_area("Parts Used", height=100)

# =========================================================
# 11. APPROVAL
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
        st.error("Sila upload signature image atau sign dalam canvas untuk kedua-dua ruangan.")
    else:
        pdf = ReportPDF(header_title=header_txt)
        logo_to_use = FIXED_LOGO_PATH if os.path.exists(FIXED_LOGO_PATH) else None

        pdf.cover_page({
            "owner": sys_owner,
            "ref": proj_ref,
            "title": selected_template,
            "loc": loc,
            "id": doc_id,
            "dt": report_dt
        }, logo_path=logo_to_use)

        temp_files_to_delete = []

        try:
            # =================================================
            # MAINTENANCE PDF
            # =================================================
            if selected_template == "MAINTENANCE REPORT":
                headers = ["NO", "ITEM / ACTIVITY", "PASS", "FAIL", "REMARK"]
                widths = [10, 110, 15, 15, 40]

                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "1.0    MAINTENANCE DETAILS / CHECKLIST", 0, 1)

                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Equipment / System Name : {equipment_name}", 0, 1)
                pdf.cell(0, 6, f"Maintenance Type : {maintenance_type}", 0, 1)
                pdf.ln(2)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, "Team Details :", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, team_details_formatted)
                pdf.ln(3)

                h_l, w_l = headers, widths
                pdf.set_font("Arial", "B", 8)
                pdf.set_fill_color(230, 230, 230)

                for i, h in enumerate(h_l):
                    pdf.cell(w_l[i], 8, h, 1, 0, "C", 1)
                pdf.ln()

                cnt = 1
                for row in maintenance_results:
                    if row["res"] == "TITLE":
                        pdf.set_font("Arial", "B", 8)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(sum(w_l), 8, f" {row['task']}", 1, 1, "L", 1)
                        cnt = 1
                    else:
                        pdf.set_font("Arial", "", 7)
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
                        pdf.cell(w_l[2], row_h, "X" if row["res"] == "PASS" else "", 1, 0, "C")
                        pdf.cell(w_l[3], row_h, "X" if row["res"] == "FAIL" else "", 1, 0, "C")

                        remark_x = curr_x + w_l[0] + w_l[1] + w_l[2] + w_l[3]
                        pdf.set_xy(remark_x, curr_y)
                        pdf.cell(w_l[4], row_h, "", 1, 0)

                        text_y = curr_y + max(0, (row_h - (line_count * 5)) / 2)
                        pdf.set_xy(remark_x, text_y)
                        pdf.multi_cell(w_l[4], 5, txt_remark, 0, "L")

                        pdf.set_xy(curr_x, curr_y + row_h)
                        cnt += 1

                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "2.0    SUMMARY", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, remarks)

                draw_attachment_grid(
                    pdf,
                    evidence_data,
                    temp_files_to_delete,
                    section_title="3.0    ATTACHMENTS"
                )

            # =================================================
            # INSTALLATION PDF
            # =================================================
            if selected_template == "INSTALLATION REPORT":
                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "1.0    SITE INFORMATION", 0, 1)

                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Customer Name : {customer_name}", 0, 1)
                pdf.multi_cell(0, 6, f"Customer Address : {customer_address}")
                pdf.cell(0, 6, f"Onsite Team / Lead : {onsite_team}", 0, 1)
                pdf.cell(0, 6, f"Onsite Date : {report_dt}", 0, 1)
                pdf.cell(0, 6, f"Start Time : {start_time}", 0, 1)
                pdf.cell(0, 6, f"Completed Time : {end_time}", 0, 1)
                pdf.cell(0, 6, f"Category : {category}", 0, 1)
                pdf.cell(0, 6, f"Service : {service}", 0, 1)
                pdf.multi_cell(0, 6, f"Problem / Scope : {problem}")
                pdf.ln(2)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, "Team Details :", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, team_details_formatted)

                pdf.ln(3)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "2.0    REMARKS", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, remarks)

                draw_attachment_grid(
                    pdf,
                    installation_results,
                    temp_files_to_delete,
                    section_title="3.0    INSTALLATION ATTACHMENTS"
                )

                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "4.0    PARTS USED", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, parts_used if parts_used.strip() else "NIL")

            # =================================================
            # APPROVAL PAGE
            # =================================================
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "APPROVAL & ACCEPTANCE", 0, 1)
            pdf.ln(5)

            pdf.set_font("Arial", "", 10)
            stmt = "The undersigned hereby confirms that the works described in this report have been carried out in accordance with the agreed scope."
            pdf.multi_cell(0, 6, stmt, 0, "L")

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
            pdf.cell(90, 8, f"PREPARED BY: {prepared_by_name}", 0, 0, "C")
            pdf.set_x(105)
            pdf.cell(90, 8, f"VERIFIED BY: {verified_by_name}", 0, 1, "C")

            pdf.set_font("Arial", "I", 8)
            pdf.set_x(15)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 0, "C")
            pdf.set_x(105)
            pdf.cell(90, 5, f"MYT: {gen_timestamp}", 0, 1, "C")

            # =================================================
            # OUTPUT
            # =================================================
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
