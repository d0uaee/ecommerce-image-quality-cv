from __future__ import annotations


BRANDS = {
    "portable_electronics": [
        "Apple",
        "Anker",
        "Baseus",
        "Bose",
        "Canon",
        "Dell",
        "DJI",
        "Google",
        "HP",
        "Huawei",
        "JBL",
        "Lenovo",
        "LG",
        "Logitech",
        "Motorola",
        "Nikon",
        "Nothing",
        "OnePlus",
        "Oppo",
        "Panasonic",
        "Philips",
        "Realme",
        "Samsung",
        "Sony",
        "TCL",
        "Xiaomi",
    ],
    "clothing": [
        "Adidas",
        "ASOS",
        "Bershka",
        "Celio",
        "Decathlon",
        "Gap",
        "H&M",
        "Kiabi",
        "Lacoste",
        "Levi's",
        "Mango",
        "Nike",
        "Puma",
        "Reebok",
        "Shein",
        "Tommy Hilfiger",
        "Uniqlo",
        "Zara",
    ],
    "shoes": [
        "Adidas",
        "Asics",
        "Clarks",
        "Converse",
        "Geox",
        "New Balance",
        "Nike",
        "Puma",
        "Reebok",
        "Skechers",
        "Timberland",
        "Vans",
        "Zara",
    ],
}


ALL_BRANDS = sorted({brand for values in BRANDS.values() for brand in values})


CATEGORY_KEYWORDS = {
    "shoes": [
        "basket",
        "bottine",
        "chaussure",
        "escarpin",
        "loafer",
        "mocassin",
        "running",
        "sandale",
        "sneaker",
        "talon",
    ],
    "clothing": [
        "blazer",
        "chemise",
        "gilet",
        "hoodie",
        "jean",
        "jupe",
        "manteau",
        "pantalon",
        "pull",
        "robe",
        "short",
        "t-shirt",
        "veste",
        "vetement",
    ],
    "portable_electronics": [
        "airpods",
        "appareil",
        "batterie externe",
        "casque",
        "chargeur",
        "ecouteurs",
        "enceinte",
        "laptop",
        "montre connectee",
        "ordinateur portable",
        "power bank",
        "smartphone",
        "tablette",
        "telephone",
        "watch",
    ],
}


FRENCH_COLOR_TO_RGB = {
    "blanc": (245, 245, 245),
    "bleu": (52, 120, 246),
    "camel": (193, 154, 107),
    "beige": (218, 201, 163),
    "bordeaux": (123, 24, 45),
    "doré": (212, 175, 55),
    "gris": (128, 128, 128),
    "jaune": (241, 196, 15),
    "kaki": (111, 124, 61),
    "marron": (124, 79, 45),
    "multicolore": (160, 120, 180),
    "noir": (28, 28, 28),
    "orange": (243, 156, 18),
    "rose": (233, 125, 161),
    "rouge": (220, 53, 69),
    "argenté": (192, 192, 192),
    "transparent": (230, 230, 230),
    "vert": (39, 174, 96),
    "violet": (142, 68, 173),
}


COLOR_ALIASES = {
    "blanc": ["blanc", "blanche", "white", "ivoire", "creme"],
    "bleu": ["bleu", "bleue", "blue", "navy", "marine", "cyan"],
    "camel": ["camel", "caramel"],
    "beige": ["beige", "sable"],
    "bordeaux": ["bordeaux", "burgundy"],
    "doré": ["dore", "doré", "gold", "golden", "or"],
    "gris": ["gris", "grise", "gray", "grey", "graphite"],
    "jaune": ["jaune", "yellow", "moutarde"],
    "kaki": ["kaki", "khaki", "olive"],
    "marron": ["marron", "brown", "brun", "chocolat"],
    "multicolore": ["multicolore", "multicolor", "imprime", "printed"],
    "noir": ["noir", "noire", "black", "ebene"],
    "orange": ["orange", "corail"],
    "rose": ["rose", "pink", "fuchsia"],
    "rouge": ["rouge", "red", "cramoisi"],
    "argenté": ["argente", "argenté", "silver", "metallic"],
    "transparent": ["transparent", "clear"],
    "vert": ["vert", "verte", "green", "menthe"],
    "violet": ["violet", "purple", "lilas", "mauve"],
}


EMBEDDING_VECTOR_SIZE = 512


if __name__ == "__main__":
    print("Categories:", list(CATEGORY_KEYWORDS.keys()))
    print("Brands:", len(ALL_BRANDS))
    print("Colors:", sorted(FRENCH_COLOR_TO_RGB.keys()))
