"""Generate a synthetic bank statement and open ledger items to reconcile.

All names and amounts are fictional. The data deliberately includes the
cases that make reconciliation painful in real life:
  - clean payments quoting the invoice number
  - payments without reference (only the customer name, sometimes misspelt)
  - one transfer paying two invoices
  - payments with a small bank fee deducted
  - bank charges and unknown items
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 7
DATA_DIR = Path(__file__).parent / "data"

CUSTOMERS = [
    "Rossi Meccanica Srl", "Bianchi Logistica SpA", "Verdi Impianti Srl", "Alpine Parts GmbH",
    "Costa Distribuzione Srl", "Nordic Motion AB", "Ferri & Figli Snc", "Lago Engineering Srl",
    "Delta Components SA", "Moretti Service Srl", "Gallo Trasporti Srl", "Orion Tech Ltd",
]
VENDORS = ["Energia Plus SpA", "Telco Business Srl", "Ufficio Pro Srl", "CloudSoft Ltd"]


def misspell(name: str, rng: random.Random) -> str:
    """Bank descriptions often truncate or uppercase the counterparty name."""
    base = name.upper().replace("SRL", "").replace("SPA", "").strip(" &")
    if rng.random() < 0.5:
        base = base[: max(8, len(base) - 4)]
    return base


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    start = date(2026, 9, 1)

    ledger, bank = [], []
    inv_no = 1200

    for i, cust in enumerate(CUSTOMERS * 2):
        inv_no += 1
        doc = f"INV-2026-{inv_no}"
        amount = round(rng.uniform(800, 25_000), 2)
        due = start + timedelta(days=rng.randint(0, 40))
        ledger.append({"Document No.": doc, "Type": "Customer invoice", "Counterparty": cust,
                       "Due Date": due.isoformat(), "Amount": amount})

        pay_date = due + timedelta(days=rng.randint(-3, 8))
        case = i % 6
        if case in (0, 1):  # clean reference
            desc = f"BONIFICO DA {cust.upper()} SALDO FT {doc}"
            bank.append((pay_date, desc, amount))
        elif case == 2:  # no reference, name only
            desc = f"BON. SEPA {misspell(cust, rng)} PAGAMENTO FATTURA"
            bank.append((pay_date, desc, amount))
        elif case == 3:  # bank fee deducted
            desc = f"BONIFICO ESTERO {misspell(cust, rng)} REF {inv_no}"
            bank.append((pay_date, desc, round(amount - rng.choice([5, 7.5, 10, 15]), 2)))
        elif case == 4:  # left open (not yet paid)
            pass
        else:  # will be paid together with the next invoice of the same customer
            ledger[-1]["_combine"] = True

    # Combined payments: two invoices, one transfer
    combine = [l for l in ledger if l.pop("_combine", False)]
    for l in combine:
        cust = l["Counterparty"]
        inv_no += 1
        doc = f"INV-2026-{inv_no}"
        amount = round(rng.uniform(500, 6_000), 2)
        due = date.fromisoformat(l["Due Date"])
        ledger.append({"Document No.": doc, "Type": "Customer invoice", "Counterparty": cust,
                       "Due Date": due.isoformat(), "Amount": amount})
        desc = f"BONIFICO {misspell(cust, rng)} PAG. FATTURE SETTEMBRE"
        bank.append((due + timedelta(days=2), desc, round(l["Amount"] + amount, 2)))

    # Vendor payments (outgoing)
    for v in VENDORS:
        inv_no += 1
        doc = f"PINV-{inv_no}"
        amount = round(rng.uniform(300, 4_000), 2)
        due = start + timedelta(days=rng.randint(5, 35))
        ledger.append({"Document No.": doc, "Type": "Vendor invoice", "Counterparty": v,
                       "Due Date": due.isoformat(), "Amount": -amount})
        bank.append((due, f"SDD {v.upper()} ADDEBITO DIRETTO", -amount))

    # Noise: bank charges and an unknown item
    bank.append((date(2026, 9, 30), "COMMISSIONI TENUTA CONTO SETTEMBRE", -18.50))
    bank.append((date(2026, 10, 1), "IMPOSTA DI BOLLO", -34.20))
    bank.append((date(2026, 9, 22), "BONIFICO DA MR J SMITH RIF 99812", 1_250.00))

    bank_df = pd.DataFrame(bank, columns=["Booking Date", "Description", "Amount"])
    bank_df["Booking Date"] = pd.to_datetime(bank_df["Booking Date"]).dt.date
    bank_df = bank_df.sort_values("Booking Date").reset_index(drop=True)
    bank_df.insert(0, "Line", range(1, len(bank_df) + 1))

    ledger_df = pd.DataFrame(ledger).sort_values("Due Date").reset_index(drop=True)

    bank_df.to_csv(DATA_DIR / "bank_statement.csv", index=False)
    ledger_df.to_csv(DATA_DIR / "open_items.csv", index=False)
    print(f"Bank lines: {len(bank_df)} | open items: {len(ledger_df)} -> {DATA_DIR}")


if __name__ == "__main__":
    main()
