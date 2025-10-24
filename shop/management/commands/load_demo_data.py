import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from shop.models import Product, Tag, Interaction

class Command(BaseCommand):
    help = 'Loads demo data from CSV files into the database.'

    def handle(self, *args, **options):
        data_dir = Path(__file__).resolve().parent.parent.parent.parent / 'data'
        products_csv = data_dir / 'products.csv'
        users_csv = data_dir / 'users.csv'
        interactions_csv = data_dir / 'interactions.csv'

        self.stdout.write("Starting data loading process...")

        try:
            with transaction.atomic():
                self.stdout.write("Clearing old data...")
                Interaction.objects.all().delete()
                Product.objects.all().delete()
                Tag.objects.all().delete()
                User.objects.filter(is_superuser=False).delete()
                self.stdout.write("Old data cleared.")

                self.stdout.write("Loading users...")
                users_df = pd.read_csv(users_csv)
                for _, row in users_df.iterrows():
                    user, created = User.objects.get_or_create(
                        username=row['username'],
                        defaults={'email': row['email'], 'first_name': row['first_name'], 'last_name': row['last_name']}
                    )
                    if created:
                        user.set_password('password')
                        user.save()
                self.stdout.write(f"{len(users_df)} users loaded.")

                self.stdout.write("Loading products and tags...")
                products_df = pd.read_csv(products_csv)
                for _, row in products_df.iterrows():
                    product = Product.objects.create(
                        id=row['id'],
                        name=row['name'],
                        description=row.get('description', ''), # <-- GET NEW FIELD
                        category=row['category'],
                        price=row['price'],
                        stock=row.get('stock', 0) # <-- GET NEW FIELD
                    )
                    tag_names = [t.strip() for t in row['tags'].split(',')]
                    for tag_name in tag_names:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        product.tags.add(tag)
                self.stdout.write(f"{len(products_df)} products loaded.")

                self.stdout.write("Loading interactions...")
                interactions_df = pd.read_csv(interactions_csv)
                for _, row in interactions_df.iterrows():
                    try:
                        user = User.objects.get(username=row['username'])
                        product = Product.objects.get(id=row['product_id'])
                        Interaction.objects.create(user=user, product=product, action=row['action'], rating=row['rating'])
                    except User.DoesNotExist:
                        self.stderr.write(f"User '{row['username']}' not found. Skipping interaction.")
                    except Product.DoesNotExist:
                        self.stderr.write(f"Product ID '{row['product_id']}' not found. Skipping interaction.")
                self.stdout.write(f"{len(interactions_df)} interactions loaded.")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
            raise e

        self.stdout.write(self.style.SUCCESS("Demo data loaded successfully!"))