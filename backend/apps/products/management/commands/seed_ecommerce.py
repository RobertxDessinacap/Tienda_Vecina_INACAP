from django.core.management.base import BaseCommand
from apps.accounts.models import UserCredential, AccountProxy
from apps.products.models import Category, Product

class Command(BaseCommand):
    help = 'Seeds initial demonstration users, categories and MercadoLibre-style products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando semillero de datos para Inacap E-Commerce...'))

        # 1. Create standard demo accounts
        admin_user, created = UserCredential.objects.get_or_create(
            email='admin@inacap.cl',
            defaults={'role': UserCredential.ROLE_ADMIN, 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('Admin1234!')
            admin_user.save()
            admin_proxy = admin_user.intermediate_account
            admin_proxy.public_alias = 'Inacap_Oficial_Store'
            admin_proxy.reputation_score = 5.00
            admin_proxy.is_verified_seller = True
            admin_proxy.save()
            self.stdout.write(self.style.SUCCESS('Creado usuario Administrador: admin@inacap.cl (Admin1234!)'))

        seller_user, created = UserCredential.objects.get_or_create(
            email='vendedor@inacap.cl',
            defaults={'role': UserCredential.ROLE_SELLER}
        )
        if created:
            seller_user.set_password('Vendedor1234!')
            seller_user.save()
            seller_proxy = seller_user.intermediate_account
            seller_proxy.public_alias = 'TechChile_Plaza'
            seller_proxy.reputation_score = 4.90
            seller_proxy.is_verified_seller = True
            seller_proxy.save()
            self.stdout.write(self.style.SUCCESS('Creado usuario Vendedor: vendedor@inacap.cl (Vendedor1234!)'))
        else:
            seller_proxy = seller_user.intermediate_account

        buyer_user, created = UserCredential.objects.get_or_create(
            email='comprador@inacap.cl',
            defaults={'role': UserCredential.ROLE_BUYER}
        )
        if created:
            buyer_user.set_password('Comprador1234!')
            buyer_user.save()
            buyer_proxy = buyer_user.intermediate_account
            buyer_proxy.public_alias = 'Cliente_Estudiante_Inacap'
            buyer_proxy.save()
            self.stdout.write(self.style.SUCCESS('Creado usuario Comprador: comprador@inacap.cl (Comprador1234!)'))

        # 2. Categories
        cat_tech, _ = Category.objects.get_or_create(name='Tecnología & Celulares', defaults={'icon_name': 'Smartphone'})
        cat_comp, _ = Category.objects.get_or_create(name='Computación & Laptops', defaults={'icon_name': 'Laptop'})
        cat_audio, _ = Category.objects.get_or_create(name='Audio & Sonido', defaults={'icon_name': 'Headphones'})
        cat_moda, _ = Category.objects.get_or_create(name='Moda & Calzado', defaults={'icon_name': 'Shirt'})
        cat_hogar, _ = Category.objects.get_or_create(name='Hogar & Muebles', defaults={'icon_name': 'Home'})

        # 3. Products
        demo_products = [
            {
                'title': 'Samsung Galaxy S24 Ultra 256GB Titanium Gray',
                'description': 'Smartphone flagship con Galaxy AI integrado, cámara cuádruple de 200MP y procesador Snapdragon 8 Gen 3. Pantalla Dynamic AMOLED 2X de 6.8 pulgadas.',
                'price': 1149990.00,
                'original_price': 1399990.00,
                'stock': 14,
                'category': cat_tech,
                'image_url': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 12,
                'rating': 4.9,
                'reviews_count': 148,
            },
            {
                'title': 'Apple MacBook Pro 14 M3 Pro 18GB RAM 512GB SSD',
                'description': 'Laptop profesional de alto rendimiento con chip M3 Pro de Apple, pantalla Liquid Retina XDR de 14.2 pulgadas y hasta 18 horas de autonomía.',
                'price': 2099990.00,
                'original_price': 2399990.00,
                'stock': 8,
                'category': cat_comp,
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 12,
                'rating': 5.0,
                'reviews_count': 92,
            },
            {
                'title': 'Audífonos Sony WH-1000XM5 Cancelación de Ruido Activa',
                'description': 'Líder en cancelación de ruido con dos procesadores y ocho micrófonos. Calidad de audio Hi-Res inalámbrico y llamadas ultra nítidas.',
                'price': 299990.00,
                'original_price': 389990.00,
                'stock': 25,
                'category': cat_audio,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.8,
                'reviews_count': 310,
            },
            {
                'title': 'Zapatillas Urbanas Nike Air Jordan 1 Retro High',
                'description': 'Diseño legendario con cuero genuino premium, amortiguación Air-Sole encapsulada y estilo atemporal para el día a día.',
                'price': 149990.00,
                'original_price': 189990.00,
                'stock': 19,
                'category': cat_moda,
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.7,
                'reviews_count': 64,
            },
            {
                'title': 'Smartwatch Garmin Forerunner 265 GPS AMOLED',
                'description': 'Reloj deportivo inteligente con pantalla táctil AMOLED de colores vibrantes, métricas de entrenamiento avanzadas y hasta 13 días de batería.',
                'price': 389990.00,
                'original_price': 449990.00,
                'stock': 11,
                'category': cat_tech,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.9,
                'reviews_count': 53,
            },
            {
                'title': 'Silla Ergonómica de Oficina Herman Miller Style Black',
                'description': 'Soporte lumbar dinámico ajustable, reposabrazos 3D y malla transpirable de alta resistencia ideal para largas jornadas de trabajo o estudio.',
                'price': 219990.00,
                'original_price': 289990.00,
                'stock': 7,
                'category': cat_hogar,
                'image_url': 'https://images.unsplash.com/photo-1580481077195-c3f99506d128?w=700&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.6,
                'reviews_count': 29,
            }
        ]

        for p_data in demo_products:
            if not Product.objects.filter(title=p_data['title']).exists():
                Product.objects.create(
                    seller_account=seller_proxy,
                    **p_data
                )
                self.stdout.write(f"Producto cargado: {p_data['title']}")

        self.stdout.write(self.style.SUCCESS('Base de datos inicializada con éxito!'))
