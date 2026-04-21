from pathlib import Path
from typing import Dict, List


DATA_DIR = Path(__file__).resolve().parent
SOURCE_DOCS_DIR = DATA_DIR / "source_docs"


DOCUMENT_SPECS = [
    {
        "id": "doc_access_control",
        "title": "Quy Trinh Kiem Soat Truy Cap He Thong",
        "topic": "quyen truy cap he thong",
        "keywords": [
            "access",
            "truy",
            "cap",
            "level",
            "jira",
            "it-access",
            "security",
            "tam",
            "thoi",
        ],
        "source_file": "access_control_sop.txt",
        "answer": (
            "Quy trinh cap quyen he thong co 4 muc truy cap, moi muc co nguoi phe duyet va SLA rieng. "
            "Truong hop khan cap chi duoc cap quyen tam thoi toi da 24 gio va phai ghi log audit."
        ),
    },
    {
        "id": "doc_hr_leave_policy",
        "title": "Chinh Sach Nghi Phep Va Remote Work",
        "topic": "nghi phep va remote work",
        "keywords": [
            "nghi",
            "phep",
            "remote",
            "hr",
            "portal",
            "vpn",
            "onsite",
            "overtime",
        ],
        "source_file": "hr_leave_policy.txt",
        "answer": (
            "Nhan vien xin nghi qua HR Portal, Line Manager duyet trong 1 ngay lam viec. "
            "Sau probation co the remote toi da 2 ngay moi tuan va phai dung VPN khi vao he thong noi bo."
        ),
    },
    {
        "id": "doc_it_helpdesk",
        "title": "IT Helpdesk FAQ",
        "topic": "ho tro helpdesk va vpn",
        "keywords": [
            "helpdesk",
            "mat",
            "khau",
            "vpn",
            "ticket",
            "it-support",
            "it-software",
            "email",
        ],
        "source_file": "it_helpdesk_faq.txt",
        "answer": (
            "Helpdesk ho tro reset mat khau, VPN, phan mem va email. "
            "Cong ty dung Cisco AnyConnect, tai khoan bi khoa sau 5 lan dang nhap sai va mat khau doi moi 90 ngay."
        ),
    },
    {
        "id": "doc_refund_policy_v4",
        "title": "Chinh Sach Hoan Tien V4",
        "topic": "hoan tien don hang",
        "keywords": [
            "refund",
            "hoan",
            "tien",
            "flash",
            "sale",
            "finance",
            "store",
            "credit",
        ],
        "source_file": "policy_refund_v4.txt",
        "answer": (
            "Chinh sach hoan tien V4 ap dung cho don hang tu 01/02/2026, yeu cau gui trong 7 ngay lam viec va chi ap dung cho don du dieu kien. "
            "Finance xu ly hoan tien trong 3-5 ngay lam viec, hoac khach co the nhan store credit 110%."
        ),
    },
    {
        "id": "doc_sla_p1",
        "title": "SLA Ticket Va Xu Ly Su Co P1",
        "topic": "sla su co p1",
        "keywords": [
            "sla",
            "p1",
            "incident",
            "response",
            "resolution",
            "pagerduty",
            "stakeholder",
        ],
        "source_file": "sla_p1_2026.txt",
        "answer": (
            "Su co P1 la muc khan cap nhat, phai first response trong 15 phut va resolve trong 4 gio. "
            "Stakeholder duoc cap nhat ngay khi nhan ticket va moi 30 phut cho den khi xong."
        ),
    },
]


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1258"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1")


def load_company_documents() -> List[Dict]:
    documents: List[Dict] = []
    for spec in DOCUMENT_SPECS:
        doc_path = SOURCE_DOCS_DIR / spec["source_file"]
        documents.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "topic": spec["topic"],
                "keywords": spec["keywords"],
                "answer": spec["answer"],
                "text": _read_text(doc_path),
                "source_file": spec["source_file"],
            }
        )
    return documents


COMPANY_DOCUMENTS = load_company_documents()
