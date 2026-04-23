#!/usr/bin/env python3
"""Generate synthetic retail-DC data for the BI demo.

Writes CSVs into:
  dbt/seeds/dc/            (dims + pallet_stock, loaded via `dbt seed`)
  scripts/out/             (fct_stock_movements.csv, loaded via COPY — too big for dbt seed)

Data shape:
  dim_dc            8 DCs across SA
  dim_category      18 categories
  dim_subcategory   ~60 subcategories
  dim_supplier      80 FMCG suppliers (SA-flavoured)
  dim_sku           ~2,500 SKUs
  dim_store         ~800 stores across banners
  fct_pallet_stock  ~35,000 active pallet positions
  fct_stock_movements  ~200,000 movements over 60 days

Deterministic — reseeding the RNG produces the same data. Safe to re-run.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

REPO = Path(__file__).resolve().parent.parent
SEEDS_DIR = REPO / "dbt" / "seeds" / "dc"
OUT_DIR = REPO / "scripts" / "out"
SEEDS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date(2026, 4, 23)


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {path.relative_to(REPO)}  ({len(rows):,} rows)")


# ---------------------------------------------------------------------------
# DCs
# ---------------------------------------------------------------------------
DCS = [
    # dc_id, dc_code, name, city, province, region, zones, capacity_pallets, temp_profile
    (1, "CIL", "Cilmor DC",             "Centurion",       "GP", "INLAND",  "AMBIENT|CHILLED|FROZEN",  65000, "MULTI"),
    (2, "CAN", "Canelands DC",          "Verulam",         "KZN","COASTAL", "AMBIENT|CHILLED",         42000, "MULTI"),
    (3, "BAS", "Basfour DC",            "Pinetown",        "KZN","COASTAL", "AMBIENT",                 38000, "AMBIENT"),
    (4, "MON", "Montague Gardens DC",   "Montague Gardens","WC", "COASTAL", "AMBIENT|CHILLED|FROZEN",  52000, "MULTI"),
    (5, "BRL", "Brackenfell Liquor DC", "Brackenfell",     "WC", "COASTAL", "AMBIENT",                 18000, "AMBIENT"),
    (6, "MID", "Midrand DC",            "Midrand",         "GP", "INLAND",  "AMBIENT|CHILLED",         36000, "MULTI"),
    (7, "ELN", "East London DC",        "East London",     "EC", "COASTAL", "AMBIENT",                 14000, "AMBIENT"),
    (8, "BFN", "Bloemfontein DC",       "Bloemfontein",    "FS", "INLAND",  "AMBIENT|CHILLED",         16000, "MULTI"),
]

write_csv(
    SEEDS_DIR / "dim_dc.csv",
    ["dc_id", "dc_code", "dc_name", "city", "province", "region", "zones", "capacity_pallets", "temp_profile"],
    [list(d) for d in DCS],
)

# ---------------------------------------------------------------------------
# Categories + subcategories
# ---------------------------------------------------------------------------
CATEGORIES = [
    # cat_id, name, zone, sku_weight (relative share)
    (1,  "Dry Groceries",          "AMBIENT", 16),
    (2,  "Bakery & Cereals",       "AMBIENT", 5),
    (3,  "Dairy & Chilled",        "CHILLED", 10),
    (4,  "Frozen Foods",           "FROZEN",  7),
    (5,  "Beverages Non-Alcoholic","AMBIENT", 8),
    (6,  "Beverages Alcoholic",    "AMBIENT", 10),
    (7,  "Confectionery & Snacks", "AMBIENT", 11),
    (8,  "Personal Care",          "AMBIENT", 8),
    (9,  "Household Cleaning",     "AMBIENT", 7),
    (10, "Baby Care",              "AMBIENT", 3),
    (11, "Pet Food",               "AMBIENT", 4),
    (12, "Health & Beauty",        "AMBIENT", 5),
    (13, "Pharmacy & Healthcare",  "AMBIENT", 3),
    (14, "Tobacco",                "AMBIENT", 2),
    (15, "Stationery",             "AMBIENT", 2),
    (16, "General Merchandise",    "AMBIENT", 3),
    (17, "Deli & Prepared",        "CHILLED", 2),
    (18, "Fresh Produce Bulk",     "AMBIENT", 2),
]

SUBCATEGORIES_BY_CAT = {
    1:  ["Rice", "Pasta", "Flour", "Sugar", "Cooking Oil", "Beans & Pulses", "Canned Vegetables", "Canned Fish", "Canned Fruit", "Sauces & Condiments", "Spices & Herbs", "Tea", "Coffee", "Breakfast Cereal"],
    2:  ["Bread", "Rolls & Buns", "Rusks", "Biscuits", "Crackers"],
    3:  ["Fresh Milk", "Long-Life Milk", "Yoghurt", "Cheese", "Butter", "Margarine", "Cream", "Eggs", "Chilled Juice"],
    4:  ["Frozen Vegetables", "Frozen Chips", "Frozen Chicken", "Frozen Fish", "Ice Cream", "Frozen Ready Meals", "Frozen Pastry"],
    5:  ["Carbonated Soft Drinks", "Fruit Juice", "Bottled Water", "Energy Drinks", "Sports Drinks", "Cordials", "Iced Tea"],
    6:  ["Beer", "Cider", "Red Wine", "White Wine", "Rose Wine", "Whisky", "Vodka", "Rum", "Brandy", "Gin", "Liqueurs", "RTD"],
    7:  ["Chocolates", "Sweets & Candy", "Chewing Gum", "Potato Chips", "Savoury Snacks", "Nuts & Seeds", "Biltong & Droewors", "Popcorn"],
    8:  ["Shampoo", "Conditioner", "Body Wash", "Bar Soap", "Deodorant", "Toothpaste", "Shaving", "Oral Care", "Hand Care"],
    9:  ["Dishwash Liquid", "Laundry Powder", "Laundry Liquid", "Fabric Softener", "Bleach", "Surface Cleaner", "Floor Care", "Toilet Care", "Air Freshener"],
    10: ["Disposable Nappies", "Baby Wipes", "Infant Formula", "Baby Food", "Baby Toiletries"],
    11: ["Dry Dog Food", "Wet Dog Food", "Dry Cat Food", "Wet Cat Food", "Pet Treats", "Small Animal Food"],
    12: ["Skincare", "Cosmetics", "Fragrance", "Hair Styling", "Hair Colour", "Sun Care"],
    13: ["OTC Medicines", "Vitamins & Supplements", "First Aid", "Feminine Hygiene", "Incontinence"],
    14: ["Cigarettes", "Tobacco & Rolling"],
    15: ["School Stationery", "Office Paper", "Writing Instruments", "Magazines"],
    16: ["Cookware", "Kitchen Disposables", "Hardware", "Small Electricals", "Toys"],
    17: ["Cold Meats", "Packaged Cheese Platters", "Prepared Salads", "Sandwiches"],
    18: ["Potatoes Bulk", "Onions Bulk", "Butternut Bulk", "Apples Bulk", "Oranges Bulk"],
}

write_csv(
    SEEDS_DIR / "dim_category.csv",
    ["category_id", "category_name", "default_zone"],
    [[c[0], c[1], c[2]] for c in CATEGORIES],
)

subcat_rows = []
subcat_id = 1
subcat_lookup = {}  # cat_id -> list of subcat_ids
for cat_id, name, zone, _weight in CATEGORIES:
    subcat_lookup[cat_id] = []
    for subname in SUBCATEGORIES_BY_CAT[cat_id]:
        subcat_rows.append([subcat_id, cat_id, subname])
        subcat_lookup[cat_id].append((subcat_id, subname))
        subcat_id += 1

write_csv(
    SEEDS_DIR / "dim_subcategory.csv",
    ["subcategory_id", "category_id", "subcategory_name"],
    subcat_rows,
)

# ---------------------------------------------------------------------------
# Suppliers (SA-flavoured FMCG)
# ---------------------------------------------------------------------------
SUPPLIER_NAMES = [
    # (name, primary_categories, own_label_for_retailer)
    ("Tiger Brands",            [1,2,5,7,9], False),
    ("AVI Limited",             [2,7,17],    False),
    ("Pioneer Foods",           [1,2,3,5],   False),
    ("RCL Foods",               [1,3,4,11],  False),
    ("Clover SA",               [3],         False),
    ("Parmalat SA",             [3],         False),
    ("Nestle SA",               [3,7,10,11], False),
    ("Unilever SA",             [8,9,3,7],   False),
    ("Procter & Gamble SA",     [8,9,10,12], False),
    ("Colgate-Palmolive SA",    [8,9],       False),
    ("Reckitt SA",              [8,9,13],    False),
    ("Johnson & Johnson SA",    [8,10,12,13],False),
    ("Kimberly-Clark SA",       [10,13],     False),
    ("Kellogg SA",              [1,2],       False),
    ("Mars SA",                 [7,11],      False),
    ("Mondelez SA",             [7],         False),
    ("Coca-Cola Beverages Africa",[5],       False),
    ("PepsiCo SA",              [5,7],       False),
    ("Simba",                   [7],         False),
    ("Distell",                 [6],         False),
    ("Heineken Beverages",      [6],         False),
    ("SAB InBev",               [6],         False),
    ("Pernod Ricard SA",        [6],         False),
    ("Diageo SA",               [6],         False),
    ("Edward Snell & Co",       [6],         False),
    ("KWV",                     [6],         False),
    ("Robertson Winery",        [6],         False),
    ("Nederburg",               [6],         False),
    ("Castle Brewing",          [6],         False),
    ("Premier Foods",           [1,2],       False),
    ("Foodcorp",                [1,7],       False),
    ("Libstar",                 [1,3,7,17],  False),
    ("McCain SA",               [4],         False),
    ("I&J",                     [4],         False),
    ("Sea Harvest",             [4],         False),
    ("Rhodes Food Group",       [1,7],       False),
    ("In2Foods",                [3,17],      False),
    ("Tongaat Hulett Sugar",    [1],         False),
    ("Illovo Sugar",            [1],         False),
    ("Freddy Hirsch",           [1],         False),
    ("Bos Brands",              [5],         False),
    ("Ceres Fruit Juices",      [5],         False),
    ("Aquazania",               [5],         False),
    ("Bakers SA",               [2],         False),
    ("Albany",                  [2],         False),
    ("Sasko",                   [1,2],       False),
    ("Tastic",                  [1],         False),
    ("Iwisa",                   [1],         False),
    ("Ace Super Maize",         [1],         False),
    ("White Star",              [1],         False),
    ("Willards",                [7],         False),
    ("Fritos",                  [7],         False),
    ("Beacon Sweets",           [7],         False),
    ("Cadbury",                 [7],         False),
    ("Lindt SA",                [7],         False),
    ("Nestle Chocolates",       [7],         False),
    ("Nik Naks",                [7],         False),
    ("Maynards",                [7],         False),
    ("Ouma Rusks",              [2],         False),
    ("Bakers Eetsumor",         [2],         False),
    ("Koo",                     [1],         False),
    ("All Gold",                [1],         False),
    ("Lucky Star",              [1],         False),
    ("Hinds",                   [1],         False),
    ("Robertsons",              [1],         False),
    ("Knorr SA",                [1],         False),
    ("Crown National",          [1],         False),
    ("Astral Foods",            [3,4,11],    False),
    ("Goldi Chicken",           [4],         False),
    ("Rainbow Chicken",         [4],         False),
    ("Bobtail",                 [11],        False),
    ("Hills Pet Nutrition SA",  [11],        False),
    ("Royal Canin SA",          [11],        False),
    ("Montis Beverages",        [5],         False),
    ("L'Oreal SA",              [12],        False),
    ("Revlon SA",               [12],        False),
    ("British American Tobacco SA",[14],     False),
    ("Philip Morris SA",        [14],        False),
    # Own-label / private label suppliers — packed for Shoprite group
    ("Ritebrand (Housebrand)",      [1,2,3,4,5,7,8,9,11], True),
    ("Oh My Goodness! (Own Label)", [1,3,4,7,8,9,10,12],  True),
    ("Simple Truth SA (Own Label)", [1,3,4,7,8,9,17],     True),
]

# Pad to 80 with regional suppliers
while len(SUPPLIER_NAMES) < 80:
    idx = len(SUPPLIER_NAMES) + 1
    SUPPLIER_NAMES.append((f"Regional Supplier {idx}", [random.randint(1, 18)], False))

suppliers = []
for i, (name, cats, own) in enumerate(SUPPLIER_NAMES[:80], start=1):
    payment_terms = random.choice(["NET30", "NET45", "NET60", "NET30", "NET30"])
    lead_days = random.choice([2, 3, 3, 4, 5, 7, 7, 10, 14])
    suppliers.append([
        i,
        f"SUP{i:04d}",
        name,
        "|".join(str(c) for c in cats),
        "OWN_LABEL" if own else "BRANDED",
        payment_terms,
        lead_days,
    ])

write_csv(
    SEEDS_DIR / "dim_supplier.csv",
    ["supplier_id", "supplier_code", "supplier_name", "category_ids", "supplier_type", "payment_terms", "lead_time_days"],
    suppliers,
)

# ---------------------------------------------------------------------------
# SKUs — weighted distribution across categories
# ---------------------------------------------------------------------------
TOTAL_SKUS = 2500
weight_total = sum(c[3] for c in CATEGORIES)

# Build a pool of suppliers per category
sup_by_cat: dict[int, list[int]] = {c[0]: [] for c in CATEGORIES}
for sup_row in suppliers:
    sup_id = sup_row[0]
    cats_str = sup_row[3]
    for c in cats_str.split("|"):
        sup_by_cat[int(c)].append(sup_id)

PACK_SIZES = {
    "Dry Groceries":        [("500g", 12), ("1kg", 10), ("2kg", 6), ("5kg", 4), ("10kg", 2)],
    "Bakery & Cereals":     [("400g", 12), ("500g", 12), ("750g", 10), ("1kg", 8)],
    "Dairy & Chilled":      [("250ml", 24), ("500ml", 20), ("1L", 12), ("2L", 6), ("125g", 24)],
    "Frozen Foods":         [("500g", 15), ("1kg", 10), ("2kg", 6), ("5kg", 4)],
    "Beverages Non-Alcoholic":[("330ml", 24), ("500ml", 12), ("1L", 12), ("1.5L", 6), ("2L", 6), ("5L", 4)],
    "Beverages Alcoholic":  [("330ml", 24), ("440ml", 24), ("500ml", 24), ("750ml", 12), ("1L", 12), ("1.75L", 6)],
    "Confectionery & Snacks":[("35g", 48), ("50g", 36), ("100g", 24), ("150g", 20), ("200g", 12), ("500g", 8)],
    "Personal Care":        [("100ml", 24), ("200ml", 18), ("400ml", 12), ("750ml", 8), ("75g", 24), ("125g", 18)],
    "Household Cleaning":   [("500ml", 12), ("750ml", 12), ("1L", 10), ("2L", 6), ("5L", 4)],
    "Baby Care":            [("Small", 8), ("Medium", 6), ("Large", 4), ("XL", 4)],
    "Pet Food":             [("400g", 24), ("1kg", 12), ("3kg", 6), ("7kg", 4), ("15kg", 2)],
    "Health & Beauty":      [("30ml", 36), ("50ml", 24), ("100ml", 18), ("200ml", 12)],
    "Pharmacy & Healthcare":[("20s", 24), ("30s", 24), ("60s", 18), ("100s", 12)],
    "Tobacco":              [("20s", 50), ("30s", 50)],
    "Stationery":           [("Each", 24), ("Pack of 5", 12), ("Pack of 10", 12)],
    "General Merchandise":  [("Each", 12), ("Pack of 2", 8), ("Pack of 4", 6)],
    "Deli & Prepared":      [("200g", 12), ("500g", 8), ("1kg", 6)],
    "Fresh Produce Bulk":   [("5kg", 50), ("10kg", 30), ("20kg", 20)],
}

CASES_PER_PALLET_BY_CAT = {
    "Dry Groceries":        (60, 96),
    "Bakery & Cereals":     (72, 120),
    "Dairy & Chilled":      (48, 80),
    "Frozen Foods":         (40, 60),
    "Beverages Non-Alcoholic":(60, 100),
    "Beverages Alcoholic":  (48, 90),
    "Confectionery & Snacks":(90, 144),
    "Personal Care":        (72, 120),
    "Household Cleaning":   (54, 96),
    "Baby Care":            (48, 72),
    "Pet Food":             (36, 60),
    "Health & Beauty":      (90, 144),
    "Pharmacy & Healthcare":(120, 180),
    "Tobacco":              (80, 120),
    "Stationery":           (60, 100),
    "General Merchandise":  (24, 60),
    "Deli & Prepared":      (48, 72),
    "Fresh Produce Bulk":   (24, 40),
}

PERISHABLE_SHELF_LIFE = {
    "Bakery & Cereals":     (3, 14),
    "Dairy & Chilled":      (7, 30),
    "Frozen Foods":         (180, 540),
    "Deli & Prepared":      (3, 10),
    "Fresh Produce Bulk":   (5, 21),
}

BASE_PRICE_BY_CAT = {
    "Dry Groceries":         (15, 120),
    "Bakery & Cereals":      (10, 60),
    "Dairy & Chilled":       (15, 90),
    "Frozen Foods":          (35, 180),
    "Beverages Non-Alcoholic":(8, 45),
    "Beverages Alcoholic":   (35, 450),
    "Confectionery & Snacks":(6, 50),
    "Personal Care":         (20, 150),
    "Household Cleaning":    (25, 130),
    "Baby Care":             (60, 300),
    "Pet Food":              (30, 250),
    "Health & Beauty":       (35, 400),
    "Pharmacy & Healthcare": (25, 200),
    "Tobacco":               (45, 120),
    "Stationery":            (10, 150),
    "General Merchandise":   (30, 800),
    "Deli & Prepared":       (45, 180),
    "Fresh Produce Bulk":    (35, 150),
}

BRAND_PREFIXES = ["Royal", "Gold", "Premium", "Classic", "Supreme", "Heritage", "Signature", "Ubuntu", "Savannah", "Table Mountain", "Kalahari", "Cape", "Highveld", "Zulu", "Umhlanga"]

skus = []
sku_id = 1
cat_lookup = {c[0]: c for c in CATEGORIES}  # id -> tuple

for cat_id, cat_name, zone, weight in CATEGORIES:
    n_skus = max(20, int(TOTAL_SKUS * weight / weight_total))
    subcats = subcat_lookup[cat_id]
    if not subcats:
        continue
    avail_sup = sup_by_cat[cat_id] or [1]
    pack_options = PACK_SIZES[cat_name]
    cases_lo, cases_hi = CASES_PER_PALLET_BY_CAT[cat_name]
    price_lo, price_hi = BASE_PRICE_BY_CAT[cat_name]
    shelf = PERISHABLE_SHELF_LIFE.get(cat_name)

    for _ in range(n_skus):
        subcat_id, subcat_name = random.choice(subcats)
        supplier_id = random.choice(avail_sup)
        sup_row = suppliers[supplier_id - 1]
        sup_name = sup_row[2]
        is_own_label = sup_row[4] == "OWN_LABEL"

        pack_size, units_per_case = random.choice(pack_options)
        cases_per_pallet = random.randint(cases_lo, cases_hi)
        unit_price = round(random.uniform(price_lo, price_hi), 2)
        case_weight_kg = round(random.uniform(2, 18), 1)

        if is_own_label:
            brand = sup_name.split(" (")[0]
        elif cat_id in (6,) and random.random() < 0.4:
            brand = sup_name  # alcoholic beverages often use supplier brand
        else:
            brand = f"{random.choice(BRAND_PREFIXES)} {subcat_name.split()[0]}" if random.random() < 0.5 else sup_name

        shelf_life = random.randint(shelf[0], shelf[1]) if shelf else None
        requires_chilled = zone == "CHILLED"
        requires_frozen = zone == "FROZEN"

        sku_code = f"SKU{sku_id:06d}"
        sku_name = f"{brand} {subcat_name} {pack_size}"

        skus.append([
            sku_id,
            sku_code,
            sku_name[:80],
            brand[:40],
            cat_id,
            subcat_id,
            supplier_id,
            pack_size,
            units_per_case,
            cases_per_pallet,
            round(case_weight_kg * cases_per_pallet, 1),
            unit_price,
            round(unit_price * units_per_case, 2),
            shelf_life if shelf_life is not None else "",
            "Y" if requires_chilled else "N",
            "Y" if requires_frozen else "N",
            "Y" if is_own_label else "N",
            "ACTIVE",
        ])
        sku_id += 1

write_csv(
    SEEDS_DIR / "dim_sku.csv",
    [
        "sku_id", "sku_code", "sku_name", "brand", "category_id", "subcategory_id",
        "supplier_id", "pack_size", "units_per_case", "cases_per_pallet",
        "pallet_weight_kg", "unit_price_zar", "case_price_zar",
        "shelf_life_days", "requires_chilled", "requires_frozen",
        "is_own_label", "status",
    ],
    skus,
)

# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------
BANNERS = [
    ("Shoprite",           450, 600, 1800),
    ("Checkers",           230, 900, 2600),
    ("Usave",              80,  250, 600),
    ("Checkers Hyper",     20,  3500, 6500),
    ("LiquorShop",         30,  150, 400),
    ("PetShop Science",    10,  180, 400),
]

PROVINCES = [
    ("GP", "Gauteng",        [1, 6], 0.28),
    ("WC", "Western Cape",   [4, 5], 0.18),
    ("KZN","KwaZulu-Natal",  [2, 3], 0.19),
    ("EC", "Eastern Cape",   [7],    0.11),
    ("FS", "Free State",     [8],    0.07),
    ("MP", "Mpumalanga",     [1, 6], 0.08),
    ("LP", "Limpopo",        [1],    0.05),
    ("NW", "North West",     [1, 8], 0.03),
    ("NC", "Northern Cape",  [8, 4], 0.01),
]

CITIES_BY_PROV = {
    "GP":  ["Johannesburg", "Pretoria", "Sandton", "Soweto", "Centurion", "Randburg", "Roodepoort", "Benoni", "Vereeniging", "Midrand", "Boksburg", "Alberton", "Kempton Park"],
    "WC":  ["Cape Town", "Bellville", "Paarl", "Stellenbosch", "Worcester", "George", "Knysna", "Mossel Bay", "Hermanus", "Oudtshoorn", "Somerset West"],
    "KZN": ["Durban", "Pietermaritzburg", "Richards Bay", "Umhlanga", "Amanzimtoti", "Ladysmith", "Empangeni", "Newcastle", "Port Shepstone"],
    "EC":  ["Gqeberha", "East London", "Mthatha", "Uitenhage", "Grahamstown", "Queenstown"],
    "FS":  ["Bloemfontein", "Welkom", "Kroonstad", "Bethlehem", "Sasolburg"],
    "MP":  ["Nelspruit", "Witbank", "Middelburg", "Secunda", "Ermelo"],
    "LP":  ["Polokwane", "Tzaneen", "Mokopane", "Thohoyandou"],
    "NW":  ["Rustenburg", "Klerksdorp", "Mahikeng", "Potchefstroom"],
    "NC":  ["Kimberley", "Upington", "Springbok"],
}

stores = []
store_id = 1
store_no_by_banner = {b[0]: 100 for b in BANNERS}
for banner, count, area_lo, area_hi in BANNERS:
    for _ in range(count):
        # pick a province weighted
        r = random.random()
        running = 0
        for code, name, dcs, share in PROVINCES:
            running += share
            if r <= running:
                prov_code, prov_name, prov_dcs = code, name, dcs
                break
        dc_id = random.choice(prov_dcs)
        # LiquorShop must use Brackenfell Liquor (dc 5) for WC, else Cilmor (1)
        if banner == "LiquorShop":
            dc_id = 5 if prov_code == "WC" else 1
        city = random.choice(CITIES_BY_PROV[prov_code])
        trading_area = random.randint(area_lo, area_hi)
        open_year = random.randint(1998, 2025)
        store_no = store_no_by_banner[banner]
        store_no_by_banner[banner] += 1
        stores.append([
            store_id,
            f"STR{store_id:05d}",
            banner,
            f"{banner} {city} #{store_no}",
            prov_code,
            prov_name,
            city,
            dc_id,
            trading_area,
            f"{open_year}-01-01",
            "OPEN",
        ])
        store_id += 1

write_csv(
    SEEDS_DIR / "dim_store.csv",
    [
        "store_id", "store_code", "banner", "store_name", "province_code",
        "province_name", "city", "primary_dc_id", "trading_area_sqm",
        "open_date", "status",
    ],
    stores,
)

# ---------------------------------------------------------------------------
# Pallet stock — current snapshot
# ---------------------------------------------------------------------------
# Targets ~55-70% utilisation against capacity_pallets in DCS (Cilmor hottest,
# regional DCs cooler). Gives the "Cilmor under pressure, East London has room"
# story in charts.
PALLETS_PER_DC = {
    1: 46800,  # Cilmor          65000 × 0.72
    2: 27720,  # Canelands       42000 × 0.66
    3: 23940,  # Basfour         38000 × 0.63
    4: 35360,  # Montague        52000 × 0.68
    5: 12600,  # Brackenfell Liq 18000 × 0.70
    6: 20880,  # Midrand         36000 × 0.58
    7:  7700,  # East London     14000 × 0.55
    8:  8320,  # Bloemfontein    16000 × 0.52
}
PALLET_TYPES = ["CHEP", "CHEP", "CHEP", "CHEP", "BLOCK", "BLOCK", "EURO"]  # weighted
STATUSES = ["PICKABLE"] * 85 + ["RESERVE"] * 8 + ["DAMAGED"] * 2 + ["QC_HOLD"] * 2 + ["EXPIRY_RISK"] * 3

# Index SKUs by zone
skus_by_zone: dict[str, list[int]] = {"AMBIENT": [], "CHILLED": [], "FROZEN": []}
for s in skus:
    sku_id_val, _, _, _, cat_id, _, _, _, _, _, _, _, _, _, req_chilled, req_frozen, _, _ = s
    zone = "FROZEN" if req_frozen == "Y" else "CHILLED" if req_chilled == "Y" else "AMBIENT"
    skus_by_zone[zone].append(sku_id_val)

# Filter each DC's allowed zones
dc_zones = {d[0]: d[6].split("|") for d in DCS}

pallet_rows = []
pallet_id_seq = 1
for dc_id, n_pallets in PALLETS_PER_DC.items():
    zones = dc_zones[dc_id]
    # Zone distribution within DC: 75% ambient, 20% chilled, 5% frozen (of allowed)
    zone_weights = []
    for z in zones:
        if z == "AMBIENT": zone_weights.append((z, 0.75))
        elif z == "CHILLED": zone_weights.append((z, 0.22))
        elif z == "FROZEN":  zone_weights.append((z, 0.08))
    total_w = sum(w for _, w in zone_weights)
    zone_weights = [(z, w / total_w) for z, w in zone_weights]

    for _ in range(n_pallets):
        r = random.random()
        running = 0
        for z, w in zone_weights:
            running += w
            if r <= running:
                zone = z
                break
        sku_pool = skus_by_zone[zone] or skus_by_zone["AMBIENT"]
        sku_ref = random.choice(sku_pool)
        sku_row = skus[sku_ref - 1]
        cases_per_pallet = sku_row[9]
        shelf_life = sku_row[13]

        qty_cases = random.randint(max(1, cases_per_pallet // 4), cases_per_pallet)
        age_days = random.choices(
            [random.randint(0, 3), random.randint(4, 14), random.randint(15, 45), random.randint(46, 120)],
            weights=[0.25, 0.45, 0.22, 0.08],
        )[0]
        received_date = TODAY - timedelta(days=age_days)
        if shelf_life:
            best_before = received_date + timedelta(days=int(shelf_life))
        else:
            best_before = ""

        aisle = chr(ord("A") + random.randint(0, 15))
        bay = random.randint(1, 50)
        level = random.randint(1, 5)

        # Introduce expiry-risk bias: if perishable and received >70% of shelf-life ago, force EXPIRY_RISK
        status_pool = STATUSES
        if shelf_life and best_before != "":
            days_left = (best_before - TODAY).days
            if days_left < 14 and days_left > 0:
                status_pool = ["EXPIRY_RISK"] * 40 + STATUSES
            elif days_left <= 0:
                status_pool = ["DAMAGED"] * 40 + STATUSES
        status = random.choice(status_pool)

        pallet_rows.append([
            f"PAL{pallet_id_seq:07d}",
            dc_id,
            sku_ref,
            zone,
            f"{aisle}-{bay:02d}-{level:02d}",
            aisle,
            bay,
            level,
            qty_cases,
            received_date.isoformat(),
            best_before.isoformat() if best_before else "",
            random.choice(PALLET_TYPES),
            status,
        ])
        pallet_id_seq += 1

write_csv(
    SEEDS_DIR / "fct_pallet_stock.csv",
    [
        "pallet_id", "dc_id", "sku_id", "zone", "bin_location",
        "aisle", "bay", "level", "qty_cases",
        "received_date", "best_before_date", "pallet_type", "status",
    ],
    pallet_rows,
)

# ---------------------------------------------------------------------------
# Stock movements — 60 days, inbound + outbound. Loaded via COPY, not dbt seed.
# ---------------------------------------------------------------------------
MOVEMENT_DAYS = 60
START = TODAY - timedelta(days=MOVEMENT_DAYS - 1)

# Store-to-DC mapping: stores ordering from their primary DC
stores_by_dc: dict[int, list[int]] = {}
for s in stores:
    stores_by_dc.setdefault(s[7], []).append(s[0])

# SKU pool per DC (based on zone compatibility)
dc_sku_pool: dict[int, list[int]] = {}
dc_sku_weights: dict[int, list[float]] = {}
for dc_id, zones in dc_zones.items():
    pool = []
    for z in zones:
        pool.extend(skus_by_zone[z])
    # Pareto velocity weight: shuffle then assign
    # 20% of SKUs → weight 20 (fast movers)
    # 30% of SKUs → weight 5  (mid)
    # 50% of SKUs → weight 1  (tail)
    # Total outbound volume share: 20% SKUs do 67%, next 30% do 25%, tail 50% do 8% — realistic Pareto.
    ranked = pool[:]
    random.shuffle(ranked)
    weights = []
    for i in range(len(ranked)):
        pct_rank = i / len(ranked)
        if   pct_rank < 0.20: weights.append(20.0)
        elif pct_rank < 0.50: weights.append(5.0)
        else:                 weights.append(1.0)
    dc_sku_pool[dc_id]    = ranked
    dc_sku_weights[dc_id] = weights

movement_path = OUT_DIR / "fct_stock_movements.csv"
mv_id = 1

# Daily rates per DC (inbound pallets, outbound store-sku case picks).
# Tuned so cover days distributes across STOCKOUT_RISK / HEALTHY / BUFFER / OVERSTOCK
# against the ~183k on-hand pallets.
INBOUND_PER_DC = {1: 220, 2: 150, 3: 135, 4: 195, 5: 65, 6: 135, 7: 55, 8: 65}
OUTBOUND_LINES_PER_DC = {1: 2100, 2: 1500, 3: 1260, 4: 1850, 5: 420, 6: 1260, 7: 480, 8: 600}

# Sunday reduction factor
def day_factor(d: date) -> float:
    return 0.25 if d.weekday() == 6 else (0.85 if d.weekday() == 5 else 1.0)

with movement_path.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "movement_id", "movement_date", "movement_type", "dc_id", "sku_id",
        "supplier_id", "store_id", "qty_cases", "qty_units",
        "unit_price_zar", "line_value_zar", "document_number",
    ])
    for day_offset in range(MOVEMENT_DAYS):
        mdate = START + timedelta(days=day_offset)
        factor = day_factor(mdate)
        for dc_id, zones in dc_zones.items():
            # Inbound — weighted by velocity (fast movers replenish more often)
            n_inbound = int(INBOUND_PER_DC[dc_id] * factor)
            for _ in range(n_inbound):
                sku_ref = random.choices(dc_sku_pool[dc_id], weights=dc_sku_weights[dc_id])[0]
                sku_row = skus[sku_ref - 1]
                supplier_id = sku_row[6]
                cases_per_pallet = sku_row[9]
                units_per_case = sku_row[8]
                unit_price = sku_row[11]
                # Inbound usually 1-2 full pallets
                pallets = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                qty_cases = cases_per_pallet * pallets
                qty_units = qty_cases * units_per_case
                line_value = round(qty_units * unit_price, 2)
                po = f"PO{mdate.strftime('%Y%m%d')}{dc_id:02d}{random.randint(1, 99999):05d}"
                w.writerow([
                    mv_id, mdate.isoformat(), "INBOUND", dc_id, sku_ref,
                    supplier_id, "", qty_cases, qty_units,
                    unit_price, line_value, po,
                ])
                mv_id += 1
            # Outbound — Pareto-weighted SKU selection
            n_outbound = int(OUTBOUND_LINES_PER_DC[dc_id] * factor)
            for _ in range(n_outbound):
                sku_ref = random.choices(dc_sku_pool[dc_id], weights=dc_sku_weights[dc_id])[0]
                sku_row = skus[sku_ref - 1]
                units_per_case = sku_row[8]
                unit_price = sku_row[11]
                store_pool = stores_by_dc.get(dc_id, [])
                if not store_pool:
                    continue
                store_id_pick = random.choice(store_pool)
                # Outbound qty represents a store replenishment order — typically
                # 1-3 pallet-equivalents of cases rather than single cases.
                banner = stores[store_id_pick - 1][2]
                if banner == "Checkers Hyper":
                    qty_cases = random.choices([60, 120, 180, 240, 360], weights=[0.15, 0.3, 0.3, 0.15, 0.1])[0]
                elif banner in ("Shoprite", "Checkers"):
                    qty_cases = random.choices([20, 40, 60, 90, 150, 240], weights=[0.15, 0.25, 0.25, 0.2, 0.1, 0.05])[0]
                elif banner == "LiquorShop":
                    qty_cases = random.choices([15, 30, 45, 60, 90],  weights=[0.25, 0.3, 0.25, 0.15, 0.05])[0]
                else:  # Usave, PetShop Science
                    qty_cases = random.choices([10, 20, 30, 50, 80], weights=[0.25, 0.3, 0.25, 0.15, 0.05])[0]
                qty_units = qty_cases * units_per_case
                line_value = round(qty_units * unit_price, 2)
                so = f"SO{mdate.strftime('%Y%m%d')}{dc_id:02d}{random.randint(1, 99999):05d}"
                w.writerow([
                    mv_id, mdate.isoformat(), "OUTBOUND", dc_id, sku_ref,
                    "", store_id_pick, qty_cases, qty_units,
                    unit_price, line_value, so,
                ])
                mv_id += 1

print(f"  wrote {movement_path.relative_to(REPO)}  ({mv_id - 1:,} rows)")
print("\nDone.")
