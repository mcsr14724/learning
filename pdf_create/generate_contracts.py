"""
Generate synthetic travel-supplier contract PDFs for ingestion/load testing.

Install:
    py -3.11 -m pip install reportlab

Generate 1,000 PDFs:
    py -3.11 generate_contracts.py --count 1000 --output generated_contracts --zip

All suppliers, properties, contacts, prices and bank details are fictional.
Do not use these documents as real contracts or payment instructions.
"""

import argparse
import random
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

SEED = 20261105

# Fictional building blocks. A numeric suffix guarantees unique supplier/property
# names even after these lists are combined.
BRANDS = [
    "Coral Dune", "Harbourlight", "Savannah Crown", "Blue Lagoon",
    "Silver Palm", "Golden Baobab", "Azure Coast", "Maple Gate",
    "Sunbird", "Moonstone", "Palm Crest", "Cedar Bay", "Kifaru Plains",
    "Amber Sands", "Ocean Pearl", "Highland Haven", "Willow Park",
    "Desert Bloom", "Misty Ridge", "Emerald Shore"
]
PROPERTY_TYPES = [
    "Island Resort", "City Hotel", "Safari Lodge", "Beach Villas",
    "Mountain Retreat", "Garden Suites", "Coastal Hotel", "River Camp",
    "Boutique Resort", "Airport Hotel"
]
DESTINATIONS = [
    ("Zanzibar, Tanzania", "USD"),
    ("Cape Town, South Africa", "ZAR"),
    ("Nairobi, Kenya", "USD"),
    ("Mombasa, Kenya", "USD"),
    ("Goa, India", "INR"),
    ("Kochi, India", "INR"),
    ("Bali, Indonesia", "IDR"),
    ("Phuket, Thailand", "THB"),
    ("Dubai, UAE", "AED"),
    ("Colombo, Sri Lanka", "USD"),
    ("Lisbon, Portugal", "EUR"),
    ("Athens, Greece", "EUR"),
    ("Kuala Lumpur, Malaysia", "MYR"),
    ("Mauritius", "EUR"),
    ("Reykjavik, Iceland", "EUR"),
]
FIRST_NAMES = [
    "Jane", "Alex", "Morgan", "Taylor", "Jordan", "Avery", "Riley",
    "Casey", "Jamie", "Cameron", "Drew", "Robin", "Sam", "Kelly",
    "Amina", "Daniel", "Priya", "Lerato", "Neema", "Arjun"
]
LAST_NAMES = [
    "Doe", "Smith", "Tan", "Patel", "Jacobs", "Kamau", "Juma",
    "Njoroge", "Miller", "Brown", "Shah", "Fernando", "Silva",
    "Khan", "Mwangi", "Perera", "Dlamini", "Wilson", "Martin"
]
ROOMS = [
    "Classic Room", "Deluxe Room", "Ocean View Room",
    "Garden Suite", "Family Suite", "Executive Studio"
]
MEAL_PLANS = ["Room Only (RO)", "Bed & Breakfast (BB)", "Half Board (HB)", "Full Board (FB)"]
CURRENCIES = {
    "USD": (120, 850), "ZAR": (1200, 8500), "INR": (4500, 28000),
    "IDR": (900000, 6500000), "THB": (2500, 18000), "AED": (400, 2600),
    "EUR": (100, 700), "MYR": (350, 2200)
}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=17, leading=21, alignment=TA_CENTER,
    textColor=HexColor("#17365D"), spaceAfter=4
))
styles.add(ParagraphStyle(
    name="SubTitle", parent=styles["Normal"], fontSize=7.5,
    leading=9, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=8
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading2"], fontSize=9.5,
    leading=12, textColor=HexColor("#17365D"),
    spaceBefore=6, spaceAfter=3
))
styles.add(ParagraphStyle(
    name="BodySmall", parent=styles["BodyText"], fontSize=7.2,
    leading=9, spaceAfter=3
))
styles.add(ParagraphStyle(
    name="CellSmall", parent=styles["BodyText"], fontSize=6.2,
    leading=7.2
))
styles.add(ParagraphStyle(
    name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=6.2, leading=7.2, textColor=colors.white
))
styles.add(ParagraphStyle(
    name="Notice", parent=styles["BodyText"], fontSize=7,
    leading=9, backColor=HexColor("#FFF2CC"),
    borderColor=HexColor("#D6B656"), borderWidth=.4,
    borderPadding=5, spaceBefore=3, spaceAfter=6
))

def para(text, style="BodySmall"):
    return Paragraph(text, styles[style])

def safe(text):
    return escape(str(text))

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 6)
    canvas.setFillColor(colors.grey)
    canvas.drawString(15 * mm, 8 * mm, "FICTIONAL TEST DATA — NOT FOR SIGNATURE OR SUPPLIER DISTRIBUTION")
    canvas.drawRightString(A4[0] - 15 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()

def make_table(rows, widths, header=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), .3, HexColor("#B8C4D1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), HexColor("#24476B")))
    t.setStyle(TableStyle(commands))
    return t

def money(currency, amount):
    return f"{currency} {amount:,.0f}"

def create_record(index, rng):
    brand = rng.choice(BRANDS)
    property_type = rng.choice(PROPERTY_TYPES)
    destination, currency = rng.choice(DESTINATIONS)
    suffix = f"{index:04d}"
    property_name = f"{brand} {property_type} {suffix}"
    supplier_name = f"{brand.replace(' ', '')} Hospitality Ltd. {suffix}"
    contact = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    product_manager = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    room_names = rng.sample(ROOMS, 3)
    meal_base = rng.choice(MEAL_PLANS)
    low, high = CURRENCIES[currency]
    base = rng.randrange(max(1, low // 10), high // 10 + 1) * 10
    rate1, rate2, rate3 = base, int(base * 1.18), int(base * 1.45)
    ref = f"TRV-{2027 + (index % 2)}-{index:05d}"
    supplier_code = f"SUP-{index:05d}"
    year = 2027 + (index % 2)

    return {
        "index": index, "brand": brand, "property_type": property_type,
        "destination": destination, "currency": currency,
        "property": property_name, "supplier": supplier_name,
        "contact": contact, "pm": product_manager,
        "rooms": room_names, "meal": meal_base,
        "rates": [rate1, rate2, rate3], "ref": ref,
        "supplier_code": supplier_code, "year": year,
        "address": f"{rng.randint(1, 250)} {rng.choice(['Coastal', 'Market', 'Palm', 'Harbour', 'Garden', 'Airport'])} Road, {destination}",
        "email": f"reservations{index:04d}@example.test",
        "phone": f"+000 555 {index:04d}",
        "valid_from": f"1 January {year}",
        "valid_to": f"31 December {year}",
    }

def build_pdf(record, destination_path):
    r = record
    cur = r["currency"]
    rates = r["rates"]
    story = [
        para(f"{safe(r['property']).upper()}<br/>SUPPLIER ACCOMMODATION AGREEMENT", "DocTitle"),
        para(f"TRAVEL SUPPLIER RATE CONTRACT • {safe(r['destination']).upper()} • TEST VERSION 1.0", "SubTitle"),
        para(
            "<b>TEST DOCUMENT:</b> This fictional contract is generated for software "
            "load testing, document ingestion, extraction, comparison and checklist "
            "workflows. All parties, property details, contacts, rates and payment "
            "details are synthetic. It is not legally binding. Do not send it to a "
            "real supplier or use its bank details.",
            "Notice"
        )
    ]

    meta = [
        [para("<b>Agreement ref.</b>", "CellSmall"), para(r["ref"], "CellSmall"),
         para("<b>Status</b>", "CellSmall"), para("Internal draft – test data", "CellSmall")],
        [para("<b>Prepared for</b>", "CellSmall"), para(r["pm"] + " | Product Manager", "CellSmall"),
         para("<b>Issue date</b>", "CellSmall"), para("5 November 2026", "CellSmall")],
        [para("<b>Supplier</b>", "CellSmall"), para(safe(r["supplier"]), "CellSmall"),
         para("<b>Destination</b>", "CellSmall"), para(safe(r["destination"]), "CellSmall")],
        [para("<b>Validity</b>", "CellSmall"), para(f"{r['valid_from']} – {r['valid_to']}", "CellSmall"),
         para("<b>Currency</b>", "CellSmall"), para(cur, "CellSmall")],
    ]
    mt = Table(meta, colWidths=[24*mm, 63*mm, 23*mm, 62*mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), HexColor("#EAF0F6")),
        ("BACKGROUND", (2,0), (2,-1), HexColor("#EAF0F6")),
        ("GRID", (0,0), (-1,-1), .3, HexColor("#B8C4D1")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 4),
    ]))
    story += [
        mt,
        para("1. Parties and purpose", "Section"),
        para(
            f"This agreement is made between <b>Northstar Travel Distribution Ltd.</b> "
            f"(Buyer) and <b>{safe(r['supplier'])}</b>, trading as "
            f"<b>{safe(r['property'])}</b> (Supplier). The Supplier will provide "
            f"accommodation and related travel services for eligible Buyer bookings "
            f"during the contract period. The parties and property are fictional test data."
        ),
        para("2. Supplier and property information", "Section"),
    ]

    profile = [
        ("Supplier code", r["supplier_code"]),
        ("Legal supplier", r["supplier"]),
        ("Property name", r["property"]),
        ("Property address", r["address"]),
        ("Reservations email", r["email"]),
        ("Contract contact", r["contact"] + " – Contracting Manager (fictional)"),
        ("Telephone", r["phone"] + " (fictional)"),
    ]
    p_rows = [[para(f"<b>{safe(k)}</b>", "CellSmall"), para(safe(v), "CellSmall")] for k, v in profile]
    story += [make_table(p_rows, [43*mm, 129*mm], header=False),
              para("3. Contract validity and seasonal terms", "Section"),
              para(
                  f"The contract applies to arrivals from <b>{r['valid_from']}</b> "
                  f"through <b>{r['valid_to']}</b>, inclusive. Rates may vary by "
                  "weekday, weekend, seasonal demand or special event dates. "
                  "No automatic renewal or rollover applies. Any extension requires "
                  "a written amendment accepted by both parties."
              )]

    rate_rows = [[para(x, "TableHead") for x in
                  ["Room type", "Meal basis", "Single", "Double", "Triple"]]]
    for i, room in enumerate(r["rooms"]):
        rate_rows.append([
            para(safe(room), "CellSmall"), para(safe(r["meal"]), "CellSmall"),
            para(money(cur, rates[i]), "CellSmall"),
            para(money(cur, int(rates[i]*1.12)), "CellSmall"),
            para(money(cur, int(rates[i]*1.28)), "CellSmall"),
        ])
    story += [
        para("4. Contracted room types and rates", "Section"),
        para(
            f"Rates are per room per night in {cur}. The following rates are "
            "illustrative net supplier rates and are subject to availability. "
            "The triple rate applies only where the room configuration permits "
            "an additional bed."
        ),
        make_table(rate_rows, [45*mm, 38*mm, 29*mm, 30*mm, 29*mm]),
        para(
            "Room descriptions, bedding configurations and photographs must be "
            "checked against the Buyer’s product/CMS record before loading."
        ),
        para("5. Meal plan and inclusions", "Section"),
        para(
            f"<b>Contracted meal basis:</b> {safe(r['meal'])}. Breakfast is included "
            "only where the selected meal basis provides it. Any lunch, dinner, "
            "beverages, activities or transfers not expressly included must be "
            "quoted separately and confirmed in writing."
        ),
        PageBreak(),
        para("6. Occupancy and child policy", "Section"),
        para(
            "Standard room occupancy is two adults. Selected room categories may "
            "accommodate a third adult or children where the Supplier confirms "
            "the bedding configuration. Infants aged 0–2 may share existing "
            "bedding subject to availability. Children aged 3–11 require the "
            "applicable child rate or written confirmation of a no-charge policy. "
            "Guests aged 12 and above are charged as adults unless a signed rate "
            "appendix states otherwise. Maximum occupancy must never be exceeded."
        ),
        para("7. Supplements and optional services", "Section"),
    ]

    extras = [
        [para(x, "TableHead") for x in ["Extra / service", "Rate", "Conditions"]],
        [para("Airport transfer", "CellSmall"), para(money(cur, int(rates[0]*.18)), "CellSmall"),
         para("Per vehicle / journey; pre-booking required", "CellSmall")],
        [para("Extra bed", "CellSmall"), para(money(cur, int(rates[0]*.12)), "CellSmall"),
         para("Per night; subject to room capacity", "CellSmall")],
        [para("Late checkout", "CellSmall"), para(money(cur, int(rates[0]*.08)), "CellSmall"),
         para("Subject to availability", "CellSmall")],
        [para("Special meal / excursion", "CellSmall"), para("On request", "CellSmall"),
         para("Must be confirmed before guest arrival", "CellSmall")],
    ]
    story += [
        make_table(extras, [45*mm, 40*mm, 87*mm]),
        para("All optional extras are excluded from the room rate unless expressly "
             "included in a confirmed booking."),
        para("8. Allocation, booking and release", "Section"),
        para(
            "The Supplier will provide indicative inventory subject to live "
            "availability. A booking is confirmed only when the Supplier issues "
            "written confirmation and a booking reference. The standard release "
            "period is 14 days before arrival. Provisional bookings are held for "
            "48 hours unless extended in writing. Group bookings and special "
            "events require a separate quotation."
        ),
        para("9. Cancellation and no-show policy", "Section"),
    ]

    cancel_rows = [
        [para("Notice before arrival", "TableHead"), para("Charge", "TableHead")],
        [para("More than 30 days", "CellSmall"), para("No accommodation cancellation charge", "CellSmall")],
        [para("15–30 days", "CellSmall"), para("30% of total accommodation value", "CellSmall")],
        [para("8–14 days", "CellSmall"), para("60% of total accommodation value", "CellSmall")],
        [para("0–7 days", "CellSmall"), para("100% of total accommodation value", "CellSmall")],
        [para("No-show / early departure", "CellSmall"), para("100% of unused confirmed nights", "CellSmall")],
    ]
    story += [
        make_table(cancel_rows, [62*mm, 110*mm]),
        para("Cancellation must be sent in writing and acknowledged by the Supplier. "
             "Third-party tickets, permits and services may carry separate charges."),
        para("10. Discounts and combinability", "Section"),
        para(
            "<b>Advance booking:</b> 7% off accommodation for bookings made at least "
            "60 days before arrival, excluding special event dates."
        ),
        para(
            "<b>Long stay:</b> 10% off accommodation for stays of 5 or more consecutive "
            "nights. The offer cannot be combined with the advance-booking discount."
        ),
        para(
            "<b>Honeymoon / anniversary:</b> A complimentary amenity may be provided "
            "for eligible stays with advance notice and supporting evidence. "
            "The benefit has no cash value."
        ),
        para("Only one monetary promotion may apply to a booking. Discounts do not "
             "apply to taxes, levies, transfers or third-party services."),
        para("11. Payment and bank-detail verification", "Section"),
        para(
            "The Supplier will invoice monthly for consumed stays. Payment is due "
            "within 30 days of receipt of a valid invoice and supporting documents. "
            "Any disputed invoice item must be raised in writing within 15 business days."
        ),
        para(
            "<b>TEST BANK DETAILS – INVALID:</b> Beneficiary: " + safe(r["supplier"]) +
            " TEST. Bank: Example Test Bank. Account: TEST-" + f"{r['index']:08d}" +
            ". SWIFT: TESTXXXX. These are synthetic placeholders and must never be "
            "used for payment.",
            "Notice"
        ),
        para(
            "Any bank-detail change must be independently verified using a previously "
            "validated supplier contact channel. Email-only instructions are insufficient. "
            "The verifier, date, method and approval must be recorded."
        ),
        PageBreak(),
        para("12. Taxes and service charges", "Section"),
        para(
            "Rates are assumed to include ordinary accommodation taxes and service "
            "charges for this test record. Any additional statutory tax or levy must "
            "be supported by an official notice showing its effective date. No "
            "unlisted surcharge may be added without written Buyer approval."
        ),
        para("13. Transfers and operating conditions", "Section"),
        para(
            "Transfers, excursions, activities and special services are excluded "
            "unless expressly included in the selected rate or confirmed in writing. "
            "The Supplier must advise the Buyer promptly of material service changes, "
            "facility closures or operational restrictions that may affect guests."
        ),
        para("14. Insurance and travel documents", "Section"),
        para(
            "Guests are responsible for appropriate travel insurance, passports, "
            "visas and entry requirements. The Supplier will provide reasonable "
            "pre-arrival information but does not guarantee entry clearance or "
            "third-party transport operations."
        ),
        para("15. Service standards and force majeure", "Section"),
        para(
            "The Supplier will maintain rooms and public facilities in safe operating "
            "condition. If a confirmed room cannot be provided, the Supplier must "
            "notify the Buyer and propose equivalent or higher-standard accommodation "
            "at no additional cost, subject to Buyer approval. Force majeure events "
            "must be notified promptly and both parties will discuss reasonable alternatives."
        ),
        para("16. Amendments and rollover", "Section"),
        para(
            "Changes to rates, room types, occupancy, meal plans, allocation, release, "
            "cancellation terms or promotions require a written amendment accepted "
            "by both parties. This agreement expires on " + safe(r["valid_to"]) +
            " and does not automatically renew."
        ),
        para("17. Confidentiality", "Section"),
        para(
            "Net rates and commercial terms are confidential and may be used only "
            "for the Buyer’s contracting, booking and distribution activities. "
            "Public publication or disclosure to unrelated third parties is prohibited "
            "except where required by law or to service a confirmed booking."
        ),
        para("18. Required addenda and supplier hand-off", "Section"),
        para(
            "A signed Commercial Agreement Addendum and signed Terms and Conditions "
            "Addendum are required in the final contract pack. Neither is attached "
            "or signed in this test version. Supplier hand-off remains blocked until "
            "both are received, checked and recorded.",
            "Notice"
        ),
        para("19. Review and signature blocks", "Section"),
        para(
            "This sample is an unsigned internal draft. Product Manager review is "
            "not supplier acceptance. No supplier hand-off or booking commitment "
            "may be made using this test document."
        ),
    ]

    signatures = [
        [para("<b>BUYER – INTERNAL REVIEW</b>", "CellSmall"),
         para("<b>SUPPLIER – ACKNOWLEDGEMENT</b>", "CellSmall")],
        [para(
            safe(r["pm"]) + "<br/>Product Manager<br/>Northstar Travel Distribution Ltd."
            "<br/><br/>Review: Pending<br/>Signature: __________________<br/>Date: __________",
            "CellSmall"),
         para(
            safe(r["contact"]) + "<br/>Contracting Manager<br/>" + safe(r["supplier"])
            + "<br/><br/>Acceptance: Not signed<br/>Signature: __________________<br/>Date: __________",
            "CellSmall")],
    ]
    story += [make_table(signatures, [86*mm, 86*mm]), PageBreak(),
              para("APPENDIX A — INTERNAL PRE-HAND-OFF CHECKLIST", "Section"),
              para(
                  "A blocking line must be green before supplier hand-off. "
                  "Non-blocking lines may be recorded as comments. These suggested "
                  "test notes are not approvals or independent verification."
              )]

    checklist = [
        ("1", "Hotel name matches CMS / product list", "BLOCKS", "Property name and supplier code supplied; CMS match not verified."),
        ("2", "Property address for new property", "COMMENT", "Synthetic address supplied."),
        ("3", "Reservations email for new / changing contact", "COMMENT", "Synthetic email supplied."),
        ("4", "Bank details for new / changing supplier", "BLOCKS", "Invalid test placeholder; real details absent."),
        ("5", "Changed bank details independently verified", "BLOCKS", "No change declared; verify if details change."),
        ("6", "Contract validity / seasonal dates / rollover", "BLOCKS", "Validity dates stated; no automatic rollover."),
        ("7", "Currency", "BLOCKS", cur + " stated."),
        ("8", "Age bands / minimum age / occupancy", "BLOCKS", "General age and occupancy rules stated; property confirmation needed."),
        ("9", "Cancellation charges", "BLOCKS", "Cancellation and no-show bands stated."),
        ("10", "Room types – load all?", "COMMENT", ", ".join(r["rooms"]) + "."),
        ("11", "Room type added", "COMMENT", "No change history supplied."),
        ("12", "Room type changed", "COMMENT", "No change history supplied."),
        ("13", "Room type removed", "COMMENT", "No change history supplied."),
        ("14", "Occupancy", "COMMENT", "Standard occupancy and exceptions described."),
        ("15", "Base meal plan clear", "BLOCKS", safe(r["meal"]) + " stated; confirm product mapping."),
        ("16", "Alternative meal plan naming / inclusions", "COMMENT", "Other meal plans require confirmation."),
        ("17", "Meal plan added", "COMMENT", "No meal-plan change history supplied."),
        ("18", "Meal plan removed", "COMMENT", "No removal history supplied."),
        ("19", "Meal plan inclusion changes", "COMMENT", "Inclusions and exclusions require product review."),
        ("20", "Allocation", "BLOCKS", "Indicative allocation; live availability applies."),
        ("21", "Release period", "BLOCKS", "14-day release and 48-hour provisional hold."),
        ("22", "Transfers / changes", "COMMENT", "Optional transfer terms stated."),
        ("23", "Gala dinners / changes", "COMMENT", "No gala dinner term; confirm if applicable."),
        ("24", "Discounts and combinability", "BLOCKS", "Advance booking, long stay and amenity terms stated."),
        ("25", "Exclusive discounts", "COMMENT", "No exclusive discount stated."),
        ("26", "Discounts staggered or total", "COMMENT", "Discount thresholds and exclusions stated."),
        ("27", "Taxes", "BLOCKS", "Tax assumptions require finance verification."),
        ("28", "Service charges", "COMMENT", "Assumed included; supplier breakdown to verify."),
        ("29", "Rollover comment", "BLOCKS", "Expiry and no automatic renewal stated."),
        ("30", "Commercial Agreement Addendum signed", "HAND-OFF BLOCK", "Not attached or signed."),
        ("31", "Terms and Conditions Addendum signed", "HAND-OFF BLOCK", "Not attached or signed."),
    ]

    rows = [[para("No.", "TableHead"), para("Checklist line", "TableHead"),
             para("Rule", "TableHead"), para("Evidence / open point", "TableHead")]]
    for n, item, rule, note in checklist:
        rows.append([para(n, "CellSmall"), para(item, "CellSmall"),
                     para(rule, "CellSmall"), para(note, "CellSmall")])
    ct = Table(rows, colWidths=[9*mm, 59*mm, 28*mm, 76*mm], repeatRows=1)
    commands = [
        ("BACKGROUND", (0,0), (-1,0), HexColor("#24476B")),
        ("GRID", (0,0), (-1,-1), .3, HexColor("#B8C4D1")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 3), ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]
    for row_index, (_, _, rule, _) in enumerate(checklist, 1):
        fill = (HexColor("#F4CCCC") if rule == "HAND-OFF BLOCK"
                else HexColor("#FCE8E6") if rule == "BLOCKS"
                else HexColor("#E2F0D9"))
        commands.append(("BACKGROUND", (2,row_index), (2,row_index), fill))
    ct.setStyle(TableStyle(commands))

    story += [
        ct, Spacer(1, 5),
        para(
            "<b>TEST HAND-OFF RESULT: BLOCKED.</b> CMS/product matching, operational "
            "bank details, tax treatment, room/meal-plan mapping and other blocking "
            "items require review. Both required addenda are unsigned and missing.",
            "Notice"
        ),
        para("APPENDIX B — DOCUMENT CONTROL", "Section"),
        para(
            "Document owner: Product Management<br/>"
            f"Internal reviewer: {safe(r['pm'])}, Product Manager<br/>"
            f"Supplier: {safe(r['supplier'])}<br/>"
            f"Property: {safe(r['property'])}<br/>"
            f"Supplier code: {r['supplier_code']}<br/>"
            f"Agreement reference: {r['ref']}<br/>"
            "Version: 1.0 – synthetic test data<br/>"
            "Purpose: contract ingestion, extraction, comparison and approval workflow testing."
        ),
    ]

    pdf = SimpleDocTemplate(
        str(destination_path), pagesize=A4,
        rightMargin=16*mm, leftMargin=16*mm,
        topMargin=12*mm, bottomMargin=16*mm,
        title=f"{r['property']} - Supplier Accommodation Agreement",
        author="Synthetic Contract Test Generator"
    )
    pdf.build(story, onFirstPage=footer, onLaterPages=footer)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic travel supplier contract PDFs.")
    parser.add_argument("--count", type=int, default=1000, help="Number of PDFs to generate (default: 1000)")
    parser.add_argument("--output", default="generated_contracts", help="Output folder")
    parser.add_argument("--zip", action="store_true", help="Also create a ZIP containing all generated PDFs")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed for repeatable output")
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    rng = random.Random(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for index in range(1, args.count + 1):
        record = create_record(index, rng)
        filename = f"Supplier_Contract_{index:04d}_{record['supplier_code']}.pdf"
        build_pdf(record, output_dir / filename)

        if index % 100 == 0 or index == args.count:
            print(f"Generated {index}/{args.count} PDFs")

    print(f"\nPDFs saved to: {output_dir.resolve()}")

    if args.zip:
        zip_path = output_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for pdf_path in sorted(output_dir.glob("*.pdf")):
                archive.write(pdf_path, arcname=pdf_path.name)
        print(f"ZIP created: {zip_path.resolve()}")

if __name__ == "__main__":
    main()
