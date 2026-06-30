from django.core.management.base import BaseCommand

from listings.models import Category, Region

REGIONS = [
    ("Andijon viloyati", "Андижанская область", "AND"),
    ("Buxoro viloyati", "Бухарская область", "BUK"),
    ("Farg'ona viloyati", "Ферганская область", "FAR"),
    ("Jizzax viloyati", "Джизакская область", "JIZ"),
    ("Namangan viloyati", "Наманганская область", "NAM"),
    ("Navoiy viloyati", "Навоийская область", "NAV"),
    ("Qashqadaryo viloyati", "Кашкадарьинская область", "QAS"),
    ("Qoraqalpog'iston Respublikasi", "Республика Каракалпакстан", "QOR"),
    ("Samarqand viloyati", "Самаркандская область", "SAM"),
    ("Sirdaryo viloyati", "Сырдарьинская область", "SIR"),
    ("Surxondaryo viloyati", "Сурхандарьинская область", "SUR"),
    ("Toshkent viloyati", "Ташкентская область", "TOV"),
    ("Toshkent shahri", "Город Ташкент", "TOS"),
    ("Xorazm viloyati", "Хорезмская область", "XOR"),
]

CATEGORIES = [
    ("Sabzavotlar", "Овощи", "sabzavot", None),
    ("Mevalar", "Фрукты", "meva", None),
    ("Sut mahsulotlari", "Молочные продукты", "sut", None),
    ("Non va shirinliklar", "Выпечка и сладости", "non-shirinlik", None),
    ("Go'sht mahsulotlari", "Мясные продукты", "gosht", None),
    ("Hunarmand mahsulotlari", "Изделия ручной работы", "hunarmand", None),
    ("Mebel", "Мебель", "mebel", None),
    ("Kiyim-kechak", "Одежда", "kiyim", None),
    ("Ulgurji mahsulotlar", "Оптовые товары", "ulgurji", None),
    ("Boshqa", "Другое", "boshqa", None),
    ("Pomidor", "Помидоры", "pomidor", "sabzavot"),
    ("Bodring", "Огурцы", "bodring", "sabzavot"),
    ("Kartoshka", "Картофель", "kartoshka", "sabzavot"),
    ("Olma", "Яблоки", "olma", "meva"),
    ("Uzum", "Виноград", "uzum", "meva"),
    ("Non", "Хлеб", "non", "non-shirinlik"),
    ("Shirinliklar", "Сладости", "shirinlik", "non-shirinlik"),
]


class Command(BaseCommand):
    help = "Seed Uzbekistan regions and marketplace categories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing regions and categories before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Category.objects.all().delete()
            Region.objects.all().delete()
            self.stdout.write("Cleared existing catalog data.")

        region_count = 0
        for name_uz, name_ru, code in REGIONS:
            _, created = Region.objects.update_or_create(
                code=code,
                defaults={"name_uz": name_uz, "name_ru": name_ru},
            )
            if created:
                region_count += 1

        parent_map = {}
        category_count = 0
        for name_uz, name_ru, slug, parent_slug in CATEGORIES:
            parent = parent_map.get(parent_slug) if parent_slug else None
            category, created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_uz": name_uz,
                    "name_ru": name_ru,
                    "parent": parent,
                },
            )
            if parent_slug is None:
                parent_map[slug] = category
            if created:
                category_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog ready: {Region.objects.count()} regions "
                f"({region_count} new), {Category.objects.count()} categories "
                f"({category_count} new)."
            )
        )
