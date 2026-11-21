"""
Generates realistic sample datasets:
1. sample_data/products.csv (E-commerce catalog)
2. sample_data/customer_tickets.xlsx (IT support & troubleshooting tickets)
"""

import os
import csv
import zipfile
import xml.sax.saxutils as saxutils

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
os.makedirs(DATA_DIR, exist_ok=True)

CSV_FILE = os.path.join(DATA_DIR, "products.csv")
XLSX_FILE = os.path.join(DATA_DIR, "customer_tickets.xlsx")

PRODUCTS = [
    {
        "sku": "AUD-001",
        "name": "AcousticPro QuietComfort Over-Ear Headphones",
        "category": "Audio",
        "price": 199.99,
        "rating": 4.8,
        "description": "Active noise cancelling wireless Bluetooth headphones with 30-hour battery life, high fidelity acoustic drivers, and memory foam earcups for long travel.",
        "stock": 45
    },
    {
        "sku": "AUD-002",
        "name": "PulseWave Waterproof Sport Earbuds",
        "category": "Audio",
        "price": 49.99,
        "rating": 4.3,
        "description": "True wireless sweatproof earbuds with IPX7 rating, secure ear hooks, deep bass boost, designed for intense running and gym workouts.",
        "stock": 120
    },
    {
        "sku": "AUD-003",
        "name": "StudioMaster Professional USB Condenser Microphone",
        "category": "Audio",
        "price": 89.50,
        "rating": 4.6,
        "description": "Cardioid studio microphone with zero-latency headphone monitoring, gain dial, pop filter, ideal for podcasting, streaming, and voiceover recording.",
        "stock": 35
    },
    {
        "sku": "FURN-101",
        "name": "ErgoFlex Executive Mesh Ergonomic Chair",
        "category": "Office Furniture",
        "price": 289.00,
        "rating": 4.9,
        "description": "Breathable high-back office chair with adjustable lumbar support, 3D armrests, tilt mechanism, and pneumatic height adjustment to prevent back pain.",
        "stock": 25
    },
    {
        "sku": "FURN-102",
        "name": "AeroRise Dual-Motor Electric Standing Desk",
        "category": "Office Furniture",
        "price": 420.00,
        "rating": 4.7,
        "description": "Solid bamboo top motorized sit-stand desk with 4 programmable height presets, anti-collision sensor, and integrated cable management tray.",
        "stock": 18
    },
    {
        "sku": "FURN-103",
        "name": "Compact Mobile Wooden Laptop Cart",
        "category": "Office Furniture",
        "price": 65.00,
        "rating": 4.1,
        "description": "Rolling space-saving side table with lockable caster wheels, rustic walnut finish, suitable for couch computing and small apartments.",
        "stock": 50
    },
    {
        "sku": "TECH-201",
        "name": "UltraView 34-Inch Curved Ultrawide Monitor",
        "category": "Electronics",
        "price": 499.99,
        "rating": 4.8,
        "description": "WQHD 3440x1440 resolution 144Hz IPS display with USB-C 90W power delivery, HDR400, split-screen picture-by-picture mode for software developers.",
        "stock": 22
    },
    {
        "sku": "TECH-202",
        "name": "TypeMaster Pro Mechanical Keyboard",
        "category": "Electronics",
        "price": 119.00,
        "rating": 4.6,
        "description": "Wireless 75% hot-swappable mechanical keyboard featuring tactile brown switches, customizable RGB backlighting, aluminum chassis, and Mac/Win toggle.",
        "stock": 70
    },
    {
        "sku": "TECH-203",
        "name": "NanoDock 12-in-1 Thunderbolt 4 Docking Station",
        "category": "Electronics",
        "price": 179.95,
        "rating": 4.5,
        "description": "High-speed dock supporting dual 4K 60Hz displays, Gigabit Ethernet, SD card reader, 100W laptop passthrough charging, and 40Gbps data transfer.",
        "stock": 40
    },
    {
        "sku": "KITCH-301",
        "name": "BaristaTouch 15-Bar Espresso & Cappuccino Machine",
        "category": "Kitchen",
        "price": 249.99,
        "rating": 4.7,
        "description": "Italian pump stainless steel espresso maker with integrated steam wand for silky microfoam milk frothing, dual temperature control, and thermoblock heating.",
        "stock": 30
    },
    {
        "sku": "KITCH-302",
        "name": "SmartBrew Digital Pour-Over Gooseneck Kettle",
        "category": "Kitchen",
        "price": 79.99,
        "rating": 4.6,
        "description": "Precision temperature kettle with 1-degree adjustments, keep-warm mode, built-in brew stopwatch, and ergonomic spout for balanced coffee pouring.",
        "stock": 65
    },
    {
        "sku": "KITCH-303",
        "name": "CrispAir 6-Quart Digital Air Fryer",
        "category": "Kitchen",
        "price": 95.00,
        "rating": 4.4,
        "description": "Rapid convection air fryer with 8 one-touch cooking presets, non-stick dishwasher-safe basket, dehydrate function, healthy frying with 85% less oil.",
        "stock": 42
    },
    {
        "sku": "FIT-401",
        "name": "TitanGrip Adjustable Cast Iron Dumbbell Set (5-50 lbs)",
        "category": "Fitness",
        "price": 310.00,
        "rating": 4.9,
        "description": "Rapid dial selection weights ranging from 5 to 50 pounds, knurled steel handle, replaces 15 sets of dumbbells for home gym strength workouts.",
        "stock": 15
    },
    {
        "sku": "FIT-402",
        "name": "ZenAlign Non-Slip Natural Rubber Yoga Mat",
        "category": "Fitness",
        "price": 54.00,
        "rating": 4.7,
        "description": "Extra thick 6mm biodegradable eco-friendly mat with alignment body lines, superior sweat grip, cushioning for joints during pilates and meditation.",
        "stock": 80
    },
    {
        "sku": "FIT-403",
        "name": "SmartTrack GPS Heart Rate Fitness Watch",
        "category": "Fitness",
        "price": 149.00,
        "rating": 4.5,
        "description": "Waterproof smart smartwatch with optical heart rate monitor, sleep stage analysis, built-in standalone GPS tracking, VO2 max estimation, 7-day battery.",
        "stock": 55
    }
]

TICKETS = [
    {
        "ticket_id": "INC-1001",
        "department": "Infrastructure",
        "priority": "Critical",
        "title": "PostgreSQL database primary disk full causing read-only failover",
        "description": "WAL archiving failed on primary db node due to disk usage reaching 99%. WAL logs filled root partition /var/lib/postgresql/data. Replication lag spiked to 45 minutes.",
        "resolution": "Ran pg_archivecleanup, purged orphan temporary tables, increased EBS volume size from 500GB to 1TB, and re-enabled automated WAL rotation."
    },
    {
        "ticket_id": "INC-1002",
        "department": "Security",
        "priority": "High",
        "title": "OAuth2 SSO login failure with token expiration loop",
        "description": "Users authenticating via Okta SAML/OAuth2 are redirected back to login screen repeatedly. Clock skew detected on application servers causing JWT validation timestamp rejects.",
        "resolution": "Synchronized system clocks using NTP chrony daemon across worker fleet and widened JWT leeway clock tolerance in auth middleware to 30 seconds."
    },
    {
        "ticket_id": "INC-1003",
        "department": "Billing",
        "priority": "Critical",
        "title": "Stripe webhook duplicate charge notifications on subscription renewals",
        "description": "Multiple customer credit cards charged twice for monthly billing renewal. Webhook listener timed out due to slow database lock and Stripe retried HTTP POST 3 times.",
        "resolution": "Implemented idempotency keys in Redis caching layer and processed webhook deliveries asynchronously in Celery background queue."
    },
    {
        "ticket_id": "INC-1004",
        "department": "Mobile App",
        "priority": "Medium",
        "title": "iOS app crashing on launch after updating to version 4.2",
        "description": "Crash reports show EXC_BAD_ACCESS in CoreData migration stack when users upgrade from app versions older than 3.8. Missing lightweight migration mapping model.",
        "resolution": "Added NSInferMappingModelAutomaticallyOption to persistent store coordinator and published hotfix release v4.2.1 to App Store."
    },
    {
        "ticket_id": "INC-1005",
        "department": "DevOps",
        "priority": "High",
        "title": "Kubernetes worker nodes OOMKilled during peak batch processing",
        "description": "Nightly ETL job processing 20GB customer analytics dumped unchunked parquet files into RAM, causing container cgroup memory limits (8Gi) to trigger OOM killer.",
        "resolution": "Modified ETL pipeline to stream data in 250MB partitions with generator iterators and adjusted Kubernetes pod memory request to 12Gi."
    },
    {
        "ticket_id": "INC-1006",
        "department": "Frontend",
        "priority": "Low",
        "title": "Dark mode styling flickering and font flash on initial page load",
        "description": "Users experience FOUC (flash of unstyled content) where bright white background appears for 200ms before user preference dark theme applies from localStorage.",
        "resolution": "Inlined theme detection script directly into HTML <head> prior to CSS render tree construction to prevent layout flashing."
    },
    {
        "ticket_id": "INC-1007",
        "department": "Data Engineering",
        "priority": "Medium",
        "title": "Kafka consumer group lag increasing on clickstream event topic",
        "description": "Consumer group 'analytics-consumer' lag exceeded 500,000 unread messages due to slow write latency into Snowflake data warehouse batch ingest.",
        "resolution": "Scaled up consumer pods from 3 to 10 instances and configured micro-batching buffer size with 5-second flushes."
    },
    {
        "ticket_id": "INC-1008",
        "department": "Security",
        "priority": "High",
        "title": "Spam bot account creation bypassing rate limits via rotating residential proxies",
        "description": "Automated attack created 4,000 fake accounts in 2 hours using rotating IP pools, bypassing standard per-IP rate limit rules.",
        "resolution": "Enabled Cloudflare Turnstile bot challenge on sign-up form and added email domain disposable address validation filter."
    }
]

def generate_csv():
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "name", "category", "price", "rating", "description", "stock"])
        writer.writeheader()
        for prod in PRODUCTS:
            writer.writerow(prod)
    print(f"-> Generated CSV: {CSV_FILE} ({len(PRODUCTS)} records)")

def create_pure_xlsx(filepath, headers, rows):
    """
    Creates a standard, valid Excel (.xlsx) file using pure standard library (zipfile + xml).
    Works without needing third-party libraries installed upfront!
    """
    # Collect shared strings
    shared_strings = []
    string_map = {}

    def get_string_idx(val):
        s = str(val)
        if s not in string_map:
            string_map[s] = len(shared_strings)
            shared_strings.append(s)
        return string_map[s]

    # Content Types
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""

    # Package Relationships
    pkg_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    # Workbook Relationships
    wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""

    # Workbook
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="CustomerTickets" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    # Build Sheet Rows
    sheet_rows_xml = []
    
    # Header row (row 1)
    col_names = ["A", "B", "C", "D", "E", "F", "G", "H"]
    header_cells = []
    for col_idx, h in enumerate(headers):
        s_idx = get_string_idx(h)
        cell_ref = f"{col_names[col_idx]}1"
        header_cells.append(f'<c r="{cell_ref}" t="s"><v>{s_idx}</v></c>')
    sheet_rows_xml.append(f'<row r="1">{"".join(header_cells)}</row>')

    # Data rows (rows 2..)
    for row_idx, row in enumerate(rows, start=2):
        row_cells = []
        for col_idx, col_name in enumerate(headers):
            val = row[col_name]
            cell_ref = f"{col_names[col_idx]}{row_idx}"
            s_idx = get_string_idx(val)
            row_cells.append(f'<c r="{cell_ref}" t="s"><v>{s_idx}</v></c>')
        sheet_rows_xml.append(f'<row r="{row_idx}">{"".join(row_cells)}</row>')

    sheet1_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    {"".join(sheet_rows_xml)}
  </sheetData>
</worksheet>"""

    # Build sharedStrings XML
    sst_entries = []
    for s in shared_strings:
        escaped = saxutils.escape(s)
        sst_entries.append(f"<si><t>{escaped}</t></si>")
    
    shared_strings_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">
  {"".join(sst_entries)}
</sst>"""

    # Pack into zip
    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", pkg_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet1_xml)
        z.writestr("xl/sharedStrings.xml", shared_strings_xml)

def generate_xlsx():
    headers = ["ticket_id", "department", "priority", "title", "description", "resolution"]
    create_pure_xlsx(XLSX_FILE, headers, TICKETS)
    print(f"-> Generated XLSX: {XLSX_FILE} ({len(TICKETS)} records)")

if __name__ == "__main__":
    generate_csv()
    generate_xlsx()
    print("Sample datasets successfully created!")
