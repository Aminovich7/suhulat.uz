import io
import os
import random
import json
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from accounts.models import SellerProfile, BuyerProfile
from listings.models import Category, Region, Listing, ListingImage
from orders.models import Order
from rfq.models import RFQ, Offer
from reviews.models import Review
from cart.models import CartItem, Cart
from wishlist.models import WishlistItem, Wishlist

User = get_user_model()

# Uzbek locations data
REGIONS_DISTRICTS = {
    "AND": ["Andijon tumani", "Asaka", "Shahrixon", "Xonobod", "Marhamat"],
    "BUK": ["Buxoro tumani", "G'ijduvon", "Qorako'l", "Kogon", "Shofirkon"],
    "FAR": ["Farg'ona tumani", "Marg'ilon", "Qo'qon", "Rishton", "Oltiariq"],
    "JIZ": ["Jizzax tumani", "Zomin", "G'allaorol", "Do'stlik"],
    "NAM": ["Namangan tumani", "Chust", "Pop", "Uychi", "Kosonsoy"],
    "NAV": ["Navoiy tumani", "Karmana", "Qiziltepa", "Nurota"],
    "QAS": ["Qarshi tumani", "Shahrisabz", "Kitob", "Koson", "G'uzor"],
    "QOR": ["Nukus tumani", "Xo'jayli", "Qo'ng'irot", "Mo'ynoq"],
    "SAM": ["Samarqand tumani", "Urgut", "Pastdarg'om", "Bulung'ur", "Toyloq"],
    "SIR": ["Guliston tumani", "Sirdaryo", "Boyovut", "Shirin"],
    "SUR": ["Termiz tumani", "Denov", "Sherobod", "Boysun", "Jarqo'rg'on"],
    "TOV": ["Chirchiq", "Angren", "Yangiyo'l", "Parkent", "Qibray", "Zangiota"],
    "TOS": ["Chilonzor", "Yunusobod", "Mirzo Ulug'bek", "Yashnobod", "Olmazor", "Uchtepa", "Mirobod", "Sergeli"],
    "XOR": ["Urganch", "Xiva", "Gurlan", "Xazorasp", "Shovot"]
}

FRUIT_TRANSLATIONS = {
    "Apple": ("Sarxil olma", "Яблоки свежие"),
    "Apricot": ("Shirin o'rik", "Абрикосы сладкие"),
    "Banana": ("Import banan", "Бананы импортные"),
    "Blackberry": ("Yangi uzilgan maymunjon", "Ежевика свежая"),
    "Blueberry": ("Foydali chernika", "Черника садовая"),
    "Cherry": ("Yirik gilos", "Крупная черешня"),
    "Durian": ("Egzotik durian", "Экзотический дуриан"),
    "Fig": ("Yangi anjir", "Свежий инжир"),
    "Grape": ("Premium uzum", "Виноград премиум"),
    "Grapes": ("Premium uzum", "Виноград премиум"),
    "Guava": ("Tropic guava", "Тропическая гуава"),
    "Kiwi": ("Laziz kivi", "Киви сочный"),
    "Lemon": ("Nordon limon", "Лимоны кислые"),
    "Lime": ("Yashil laym", "Лайм зеленый"),
    "Lychee": ("Shirin lichi", "Личи сладкий"),
    "Mango": ("Pishgan mango", "Спелое манго"),
    "Melon": ("Sershira qovun", "Сочная дыня"),
    "Orange": ("Shirin apelsin", "Апельсины сладкие"),
    "Papaya": ("Tropic papayya", "Папайя тропическая"),
    "Pear": ("Asal nok", "Груша медовая"),
    "Persimmon": ("Shirin xurmo", "Сладкая хурма"),
    "Pineapple": ("Yirik ananas", "Крупный ананас"),
    "Plum": ("Qora olxo'ri", "Слива черная"),
    "Raspberry": ("Sarxil malina", "Свежая малина"),
    "Strawberry": ("Yangi uzilgan qulupnay", "Свежая клубника"),
    "Tomato": ("Issiqxona pomidori", "Тепличные помидоры"),
    "Watermelon": ("Shirin tarvuz", "Сладкий арбуз")
}

FALLBACK_FRUITS = [
    {
        "name": "Strawberry",
        "family": "Rosaceae",
        "genus": "Fragaria",
        "nutritions": {"calories": 29, "carbohydrates": 5.5, "protein": 0.8, "fat": 0.4, "sugar": 5.4}
    },
    {
        "name": "Banana",
        "family": "Musaceae",
        "genus": "Musa",
        "nutritions": {"calories": 96, "carbohydrates": 22.0, "protein": 1.0, "fat": 0.2, "sugar": 17.2}
    },
    {
        "name": "Apple",
        "family": "Rosaceae",
        "genus": "Malus",
        "nutritions": {"calories": 52, "carbohydrates": 13.8, "protein": 0.3, "fat": 0.2, "sugar": 10.3}
    },
    {
        "name": "Grape",
        "family": "Vitaceae",
        "genus": "Vitis",
        "nutritions": {"calories": 69, "carbohydrates": 18.1, "protein": 0.7, "fat": 0.2, "sugar": 16.0}
    },
    {
        "name": "Orange",
        "family": "Rutaceae",
        "genus": "Citrus",
        "nutritions": {"calories": 47, "carbohydrates": 11.8, "protein": 0.9, "fat": 0.1, "sugar": 9.4}
    },
    {
        "name": "Peach",
        "family": "Rosaceae",
        "genus": "Prunus",
        "nutritions": {"calories": 39, "carbohydrates": 9.5, "protein": 0.9, "fat": 0.3, "sugar": 8.4}
    },
    {
        "name": "Pineapple",
        "family": "Bromeliaceae",
        "genus": "Ananas",
        "nutritions": {"calories": 50, "carbohydrates": 13.1, "protein": 0.5, "fat": 0.1, "sugar": 9.95}
    },
    {
        "name": "Cherry",
        "family": "Rosaceae",
        "genus": "Prunus",
        "nutritions": {"calories": 50, "carbohydrates": 12.0, "protein": 1.0, "fat": 0.3, "sugar": 8.0}
    },
    {
        "name": "Watermelon",
        "family": "Cucurbitaceae",
        "genus": "Citrullus",
        "nutritions": {"calories": 30, "carbohydrates": 8.0, "protein": 0.6, "fat": 0.2, "sugar": 6.0}
    },
    {
        "name": "Tomato",
        "family": "Solanaceae",
        "genus": "Solanum",
        "nutritions": {"calories": 18, "carbohydrates": 3.9, "protein": 0.9, "fat": 0.2, "sugar": 2.6}
    }
]

FALLBACK_PRODUCTS = [
    {
        "title": "Essence Mascara Lash Princess",
        "description": "The Essence Mascara Lash Princess is a popular mascara known for its volumizing and lengthening effects. It features a specially-designed fiber brush that coats each lash.",
        "category": "beauty",
        "price": 9.99
    },
    {
        "title": "Eyeshadow Palette with 12 Shades",
        "description": "Create stunning eye looks with this eyeshadow palette featuring 12 rich and highly pigmented shades ranging from neutrals to bold pops of color.",
        "category": "beauty",
        "price": 19.99
    },
    {
        "title": "Powder Canister",
        "description": "Keep your makeup fresh all day with this loose setting powder canister. It absorbs excess oil and provides a matte finish without drying your skin.",
        "category": "beauty",
        "price": 14.99
    },
    {
        "title": "Red Lipstick",
        "description": "Make a bold statement with this classic red matte lipstick. Formulated with hydrating ingredients for comfortable, long-lasting wear.",
        "category": "beauty",
        "price": 12.99
    },
    {
        "title": "Classic Wood Furniture Table",
        "description": "Crafted from high-quality solid wood, this elegant dining table features a classic design that fits beautifully in any home decor.",
        "category": "furniture",
        "price": 120.00
    },
    {
        "title": "Leather Sofa",
        "description": "Relax in luxury with this premium three-seater leather sofa. Built with a sturdy wooden frame and soft, durable top-grain leather.",
        "category": "furniture",
        "price": 450.00
    },
    {
        "title": "Office Ergonomic Chair",
        "description": "Boost your productivity with this ergonomic office chair. Features adjustable height, armrests, and dynamic lumbar support.",
        "category": "furniture",
        "price": 180.00
    },
    {
        "title": "Men's Cotton T-Shirt",
        "description": "Stay comfortable and stylish with this 100% premium cotton crewneck t-shirt. Ideal for casual daily wear or active lifestyle.",
        "category": "clothing",
        "price": 15.00
    },
    {
        "title": "Women's Leather Handbag",
        "description": "A chic and spacious leather handbag featuring multiple compartments, a secure zip closure, and comfortable handles.",
        "category": "clothing",
        "price": 75.00
    },
    {
        "title": "Running Sports Shoes",
        "description": "Designed for maximum comfort and speed, these running shoes feature a lightweight mesh upper and cushioned midsole.",
        "category": "clothing",
        "price": 60.00
    }
]

def generate_dummy_image(title, category_type):
    # Determine colors based on listing type
    if category_type == 'surplus':
        bg_color = (46, 125, 50)  # Forest Green
        accent_color = (255, 235, 59) # Yellow
    elif category_type == 'maker':
        bg_color = (141, 110, 99)  # Clay/Brown
        accent_color = (255, 171, 64) # Orange
    else:
        bg_color = (21, 101, 192)  # Ocean Blue
        accent_color = (0, 229, 255) # Cyan

    # Create base image
    img = Image.new("RGB", (600, 450), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw background modern geometric accents
    draw.ellipse([(-60, -60), (280, 280)], fill=(bg_color[0]+20, bg_color[1]+20, bg_color[2]+20))
    draw.ellipse([(380, 220), (720, 560)], fill=(max(0, bg_color[0]-25), max(0, bg_color[1]-25), max(0, bg_color[2]-25)))
    
    # Draw central decorative shape based on category type
    if category_type == 'surplus':
        # Green leaves & Red Tomato/Fruit shape
        draw.ellipse([(220, 90), (380, 250)], fill=(229, 57, 53)) # Red body
        draw.rectangle([(290, 70), (310, 100)], fill=(76, 175, 80)) # Stem
        draw.polygon([(310, 75), (340, 60), (310, 90)], fill=(76, 175, 80)) # Leaf
    elif category_type == 'maker':
        # Ceramic / Pot shape
        draw.chord([(210, 110), (390, 270)], start=0, end=180, fill=(255, 243, 224), outline=accent_color, width=5)
        draw.line([(210, 190), (390, 190)], fill=accent_color, width=6)
        draw.ellipse([(280, 140), (320, 180)], fill=bg_color)
    else:
        # Logistic box shape
        draw.rectangle([(220, 110), (380, 250)], fill=(244, 208, 111), outline=(188, 143, 143), width=5)
        draw.line([(220, 180), (380, 180)], fill=(188, 143, 143), width=3)
        draw.line([(300, 110), (300, 250)], fill=(188, 143, 143), width=3)

    # Watermark branding
    draw.text((25, 25), "suhulat.uz", fill=accent_color)

    # Black panel for text contrast
    draw.rectangle([(0, 320), (600, 450)], fill=(20, 20, 20, 180))
    
    # Load fonts, default back to load_default if error
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Draw Text
    draw.text((35, 340), title[:38] + ("..." if len(title) > 38 else ""), fill=(255, 255, 255), font=font_title)
    
    cat_label = {
        'surplus': "Hosil (Surplus Product)",
        'maker': "Hunarmandchilik (Handicraft)",
        'wholesale': "Optom Savdo (Wholesale)"
    }[category_type]
    
    draw.text((35, 385), f"Kategoriya: {cat_label}", fill=accent_color, font=font_sub)
    draw.text((35, 410), "Sertifikatlangan Sotuvchi", fill=(200, 200, 200), font=font_sub)

    # Output to BytesIO
    out_io = io.BytesIO()
    img.save(out_io, format='JPEG', quality=90)
    out_io.seek(0)
    return ContentFile(out_io.read(), name=f"{category_type}_{random.randint(1000, 9999)}.jpg")

def download_image_file(category, img_id, fallback_title, fallback_type, stdout=None):
    cache_dir = os.path.join(str(settings.MEDIA_ROOT), 'seed_cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_filename = f"static_photos_{category}_{img_id}.webp"
    cache_filepath = os.path.join(cache_dir, cache_filename)

    # Check if cached file exists
    if os.path.exists(cache_filepath):
        try:
            with open(cache_filepath, 'rb') as f:
                img_data = f.read()
            if len(img_data) > 1000:
                if stdout:
                    stdout.write(f"Using cached image {cache_filename}")
                return ContentFile(img_data, name=f"{category}_{img_id}.webp")
        except Exception as e:
            if stdout:
                stdout.write(f"Failed to read cached image {cache_filename}: {e}")

    # Fetch from Static.Photos
    url = f"https://static.photos/{category}/600x450/{img_id}.webp"
    if stdout:
        stdout.write(f"Downloading image from Static.Photos: {url}...")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            img_data = response.read()
            if len(img_data) > 1000:
                with open(cache_filepath, 'wb') as f:
                    f.write(img_data)
                return ContentFile(img_data, name=f"{category}_{img_id}.webp")
            else:
                raise ValueError("Downloaded file too small, likely not a valid image")
    except Exception as e:
        if stdout:
            stdout.write(f"Failed to download image from {url}: {e}. Falling back to generated dummy image.")

    # Fallback to generating dummy image
    return generate_dummy_image(fallback_title, fallback_type)


class Command(BaseCommand):
    help = "Seed exactly 20 high-quality dummy listings with real pictures from Fruityvice, DummyJSON, and Static.Photos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing test listings and users before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing orders, RFQs, reviews, wishlist, cart, listings...")
            Order.objects.all().delete()
            Offer.objects.all().delete()
            RFQ.objects.all().delete()
            Review.objects.all().delete()
            CartItem.objects.all().delete()
            Cart.objects.all().delete()
            WishlistItem.objects.all().delete()
            Wishlist.objects.all().delete()
            ListingImage.objects.all().delete()
            Listing.objects.all().delete()
            
            # Delete only test users to avoid bricking existing accounts
            self.stdout.write("Deleting test users...")
            User.objects.filter(phone__startswith="+998901").delete()
            User.objects.filter(phone__startswith="+998902").delete()
            User.objects.filter(phone__startswith="+998903").delete()
            User.objects.filter(phone__startswith="+998904").delete()
            self.stdout.write("Existing test listings and users cleared.")

        # Ensure regions and categories are populated
        if not Region.objects.exists() or not Category.objects.exists():
            self.stdout.write("Base catalog missing. Running seed_catalog...")
            call_command("seed_catalog")

        regions = list(Region.objects.all())
        categories = list(Category.objects.all())

        if not regions or not categories:
            self.stdout.write(self.style.ERROR("Could not load regions/categories. Aborting."))
            return

        # Map categories by slug for easy lookups
        categories_by_slug = {c.slug: c for c in categories}

        self.stdout.write("Creating test users...")
        
        # Helper to create user & profile
        def get_or_create_seller(phone, full_name, seller_name, seller_type):
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "full_name": full_name,
                    "role": User.Role.SELLER,
                    "is_active": True
                }
            )
            if created:
                user.set_password("password123")
                user.save()
            
            region_item = random.choice(regions)
            code = region_item.code if region_item.code in REGIONS_DISTRICTS else "TOS"
            district_item = random.choice(REGIONS_DISTRICTS[code])
            
            profile, p_created = SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "seller_name": seller_name,
                    "seller_type": seller_type,
                    "region": region_item,
                    "district": district_item,
                    "description": f"Suhulat platformasida rasmiy hamkorimiz {seller_name}.",
                    "is_verified": True,
                    "rating": random.choice([4.2, 4.5, 4.8, 5.0]),
                    "total_reviews": random.randint(5, 40)
                }
            )
            if not p_created:
                profile.is_verified = True
                profile.save()
            return user

        def get_or_create_buyer(phone, full_name, is_business=False, company_name=""):
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "full_name": full_name,
                    "role": User.Role.BUYER,
                    "is_active": True
                }
            )
            if created:
                user.set_password("password123")
                user.save()
            
            region_item = random.choice(regions)
            code = region_item.code if region_item.code in REGIONS_DISTRICTS else "TOS"
            district_item = random.choice(REGIONS_DISTRICTS[code])

            BuyerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "region": region_item,
                    "district": district_item,
                    "is_business_buyer": is_business,
                    "company_name": company_name if is_business else "",
                    "rating": random.choice([4.0, 4.5, 4.7]),
                    "total_reviews": random.randint(1, 10)
                }
            )
            return user

        # Create Sellers
        hosil_sellers = [
            get_or_create_seller("+998901111111", "Hosilchi Dehqon 1", "Dehqon Chilonzor", SellerProfile.SellerType.SURPLUS),
            get_or_create_seller("+998901111112", "Hosilchi Dehqon 2", "Sergeli Hosili", SellerProfile.SellerType.SURPLUS),
            get_or_create_seller("+998901111113", "Hosilchi Dehqon 3", "Yunusobod Agro", SellerProfile.SellerType.SURPLUS)
        ]

        maker_sellers = [
            get_or_create_seller("+998902222221", "Hunarmand Usta 1", "Marg'ilon Ipakchisi", SellerProfile.SellerType.MAKER),
            get_or_create_seller("+998902222222", "Hunarmand Usta 2", "Rishton Kulolchiligi", SellerProfile.SellerType.MAKER),
            get_or_create_seller("+998902222223", "Hunarmand Usta 3", "Buxoro Zardo'zligi", SellerProfile.SellerType.MAKER)
        ]

        wholesale_sellers = [
            get_or_create_seller("+998903333331", "Optomchi Savdogar 1", "Tashkent Wholesale Trade", SellerProfile.SellerType.WHOLESALE),
            get_or_create_seller("+998903333332", "Optomchi Savdogar 2", "Oloy Bozori Optom", SellerProfile.SellerType.WHOLESALE),
            get_or_create_seller("+998903333333", "Optomchi Savdogar 3", "Sirdaryo Logistics Optom", SellerProfile.SellerType.WHOLESALE)
        ]

        # Create Buyers
        get_or_create_buyer("+998904444441", "Xaridor Buyer 1", is_business=True, company_name="Suhulat Trade LLC")
        get_or_create_buyer("+998904444442", "Xaridor Buyer 2", is_business=True, company_name="AgroExport UZ")
        get_or_create_buyer("+998904444443", "Xaridor Buyer 3")
        get_or_create_buyer("+998904444444", "Xaridor Buyer 4")
        get_or_create_buyer("+998904444445", "Xaridor Buyer 5")

        self.stdout.write("Test users ready. Fetching data from APIs...")

        # Fetch Fruityvice fruits (10 items)
        fruits_list = []
        try:
            req = urllib.request.Request("https://www.fruityvice.com/api/fruit/all", headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=10)
            fruits_all = json.loads(res.read().decode('utf-8'))
            fruits_list = fruits_all[:10]
            self.stdout.write(f"Successfully fetched {len(fruits_list)} fruits from Fruityvice API.")
        except Exception as e:
            self.stdout.write(f"Failed to fetch fruits from Fruityvice: {e}. Using fallback fruit data.")
            fruits_list = FALLBACK_FRUITS[:10]

        # Fetch DummyJSON products (10 items with diverse categories)
        products_list = []
        try:
            req = urllib.request.Request("https://dummyjson.com/products?limit=100", headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=10)
            products_data = json.loads(res.read().decode('utf-8'))
            products_all = products_data.get("products", [])
            
            # Group products by categories to ensure diversity
            categorized_groups = {}
            for prod in products_all:
                api_cat = prod.get("category", "other").lower()
                if "furniture" in api_cat or "decoration" in api_cat or "kitchen" in api_cat:
                    target_cat = "studio"
                elif "beauty" in api_cat or "cosmetics" in api_cat or "care" in api_cat or "fragrance" in api_cat:
                    target_cat = "cosmetic"
                elif "laptop" in api_cat or "phone" in api_cat or "tablet" in api_cat or "device" in api_cat or "technology" in api_cat:
                    target_cat = "technology"
                elif "groceries" in api_cat or "food" in api_cat:
                    target_cat = "food"
                elif "shirt" in api_cat or "shoe" in api_cat or "dress" in api_cat or "bag" in api_cat or "wear" in api_cat or "clothing" in api_cat or "jewellery" in api_cat:
                    target_cat = "retail"
                else:
                    target_cat = "other"
                
                if target_cat not in categorized_groups:
                    categorized_groups[target_cat] = []
                categorized_groups[target_cat].append(prod)

            target_cats_order = ["studio", "cosmetic", "technology", "food", "retail", "other"]
            while len(products_list) < 10 and any(categorized_groups.values()):
                for cat in target_cats_order:
                    if cat in categorized_groups and categorized_groups[cat]:
                        prod = categorized_groups[cat].pop(0)
                        products_list.append(prod)
                        if len(products_list) >= 10:
                            break

            self.stdout.write(f"Successfully fetched {len(products_list)} diverse products from DummyJSON API.")
        except Exception as e:
            self.stdout.write(f"Failed to fetch products from DummyJSON: {e}. Using fallback product data.")
            products_list = FALLBACK_PRODUCTS[:10]

        total_created = 0

        # Seeding 10 Fruits / Vegetables from Fruityvice
        self.stdout.write("Seeding 10 listings from Fruityvice...")
        for index, fruit in enumerate(fruits_list):
            eng_name = fruit.get("name", "Fruit")
            family = fruit.get("family", "Unknown")
            genus = fruit.get("genus", "Unknown")
            nutritions = fruit.get("nutritions", {})
            
            # Map name to Uzbek and Russian using translation dict
            names = FRUIT_TRANSLATIONS.get(eng_name, (f"Yangiligida {eng_name}", f"Свежий {eng_name}"))
            title_uz, title_ru = names
            
            # Categories mapping
            cat_slug = "meva"
            if eng_name.lower() == "tomato":
                cat_slug = "pomidor"
            elif eng_name.lower() == "apple":
                cat_slug = "olma"
            elif eng_name.lower() in ["grape", "grapes"]:
                cat_slug = "uzum"
            
            cat = categories_by_slug.get(cat_slug, categories_by_slug.get("meva", categories[0]))
            region = random.choice(regions)
            code = region.code if region.code in REGIONS_DISTRICTS else "TOS"
            district = random.choice(REGIONS_DISTRICTS[code])
            
            # Assign to Hosil dehqon (surplus) seller
            seller = random.choice(hosil_sellers)
            
            # Price in UZS
            price = random.randint(12000, 35000)
            qty = round(random.uniform(50.0, 500.0), 1)
            
            desc = (
                f"Tabiiy va eko-toza sharoitda yetishtirilgan mahsulot.\n\n"
                f"Tasnifi:\n"
                f"- Oilasi (Family): {family}\n"
                f"- Turkumi (Genus): {genus}\n\n"
                f"Ozuqaviy qiymati (100g uchun):\n"
                f"- Kaloriya (Calories): {nutritions.get('calories', 0)} kcal\n"
                f"- Uglevodlar (Carbohydrates): {nutritions.get('carbohydrates', 0)}g\n"
                f"- Oqsillar (Protein): {nutritions.get('protein', 0)}g\n"
                f"- Yog'lar (Fat): {nutritions.get('fat', 0)}g\n"
                f"- Shakar (Sugar): {nutritions.get('sugar', 0)}g\n\n"
                f"Sifati a'lo darajada. To'g'ridan-to'g'ri bog'imizdan uzib yetkaziladi."
            )
            
            listing = Listing.objects.create(
                seller=seller,
                title=f"{title_uz} (Eko #{index+1})",
                description=desc,
                category=cat,
                region=region,
                district=district,
                listing_type=random.choice([Listing.ListingType.FIXED, Listing.ListingType.NEGOTIABLE]),
                price=price if index % 5 != 0 else None,
                currency="UZS",
                quantity_available=qty,
                unit=Listing.Unit.KG,
                minimum_order_quantity=random.choice([1, 5, 10]),
                is_perishable=True,
                expires_at=timezone.now() + timezone.timedelta(days=random.randint(5, 20)),
                status=Listing.Status.ACTIVE
            )
            
            # Pairing fruit with Static.Photos category 'food'
            img_id = (index % 10) + 1
            img_file = download_image_file("food", img_id, listing.title, "surplus", self.stdout)
            
            ListingImage.objects.create(
                listing=listing,
                image=img_file,
                order=1
            )
            total_created += 1

        # Seeding 10 General Products from DummyJSON
        self.stdout.write("Seeding 10 listings from DummyJSON...")
        for index, prod in enumerate(products_list):
            title = prod.get("title", f"General Product #{index+1}")
            desc_api = prod.get("description", "Premium quality product.")
            api_cat = prod.get("category", "other").lower()
            price_usd = prod.get("price", 10.0)
            
            # Map category in Django
            cat_slug = "boshqa"
            static_category = "retail"
            seller_pool = wholesale_sellers
            unit_val = Listing.Unit.PIECE
            is_wholesale = False
            
            if "furniture" in api_cat or "decoration" in api_cat or "kitchen" in api_cat:
                cat_slug = "mebel"
                static_category = "studio"
                seller_pool = maker_sellers
            elif "beauty" in api_cat or "cosmetics" in api_cat or "care" in api_cat or "fragrance" in api_cat:
                cat_slug = "boshqa"
                static_category = "cosmetic"
                seller_pool = maker_sellers
            elif "laptop" in api_cat or "phone" in api_cat or "tablet" in api_cat or "device" in api_cat or "technology" in api_cat:
                cat_slug = "boshqa"
                static_category = "technology"
                seller_pool = wholesale_sellers
                is_wholesale = True
            elif "groceries" in api_cat or "food" in api_cat:
                cat_slug = "ulgurji"
                static_category = "food"
                seller_pool = wholesale_sellers
                is_wholesale = True
                unit_val = Listing.Unit.BOX
            elif "shirt" in api_cat or "shoe" in api_cat or "dress" in api_cat or "bag" in api_cat or "wear" in api_cat or "clothing" in api_cat:
                cat_slug = "kiyim"
                static_category = "retail"
                seller_pool = maker_sellers
            elif "jewellery" in api_cat:
                cat_slug = "hunarmand"
                static_category = "retail"
                seller_pool = maker_sellers
            
            cat = categories_by_slug.get(cat_slug, categories_by_slug.get("boshqa", categories[0]))
            region = random.choice(regions)
            code = region.code if region.code in REGIONS_DISTRICTS else "TOS"
            district = random.choice(REGIONS_DISTRICTS[code])
            
            seller = random.choice(seller_pool)
            
            # Convert price to UZS
            price_uzs = round((price_usd * 12500) / 1000) * 1000
            if price_uzs == 0:
                price_uzs = 15000
                
            qty = random.randint(10, 100) if not is_wholesale else random.randint(100, 1000)
            min_order = random.choice([1, 2, 5]) if not is_wholesale else random.choice([10, 20, 50])
            
            description = (
                f"{desc_api}\n\n"
                f"Kafolatlangan sifat. Mahsulotimiz to'liq sertifikatlangan.\n"
                f"Kategoriya: {api_cat.capitalize()}\n"
                f"Ulgurji xaridorlar va hamkorlar uchun qo'shimcha chegirmalar taqdim etiladi."
            )
            
            listing = Listing.objects.create(
                seller=seller,
                title=f"{title} (Premium #{index+1})",
                description=description,
                category=cat,
                region=region,
                district=district,
                listing_type=random.choice([Listing.ListingType.FIXED, Listing.ListingType.NEGOTIABLE]),
                price=price_uzs if index % 4 != 0 else None,
                currency="UZS",
                quantity_available=qty,
                unit=unit_val,
                minimum_order_quantity=min_order,
                is_perishable=False,
                expires_at=None,
                status=Listing.Status.ACTIVE
            )
            
            # Pairing product with Static.Photos categorized image
            img_id = (index % 10) + 1
            seller_type_str = "maker" if seller_pool == maker_sellers else "wholesale"
            img_file = download_image_file(static_category, img_id, listing.title, seller_type_str, self.stdout)
            
            ListingImage.objects.create(
                listing=listing,
                image=img_file,
                order=1
            )
            total_created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {total_created} high-quality listings!"))
