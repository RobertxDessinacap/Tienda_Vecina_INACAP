from django.core.management.base import BaseCommand
from apps.accounts.models import UserCredential, UserProfile, Persona, Rol, UserRol
from apps.products.models import Category, Product

class Command(BaseCommand):
    help = 'Seeds initial demonstration users, Persona objects, UserProfiles, Roles and MercadoLibre-style products.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando semillero de datos de arquitectura User-UserProfile-Persona...'))

        # 1. Crear Roles del Sistema
        rol_admin, _ = Rol.objects.get_or_create(
            codigo='ADMIN',
            defaults={'nombre': 'Administrador del Sistema', 'descripcion': 'Control total de la plataforma'}
        )
        rol_seller, _ = Rol.objects.get_or_create(
            codigo='SELLER',
            defaults={'nombre': 'Vendedor Autorizado', 'descripcion': 'Permiso para publicar y vender productos'}
        )
        rol_buyer, _ = Rol.objects.get_or_create(
            codigo='BUYER',
            defaults={'nombre': 'Cliente / Comprador', 'descripcion': 'Navegación y compra segura'}
        )

        # 2. Cuentas Demo con User, Persona y UserProfile
        admin_user, created = UserCredential.objects.get_or_create(
            email='admin@inacap.cl',
            defaults={'role': UserCredential.ROLE_ADMIN, 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('Admin1234!')
            admin_user.save()
            admin_profile = admin_user.user_profile
            admin_profile.public_alias = 'Inacap_Oficial_Store'
            admin_profile.persona.nombres = 'Administrador'
            admin_profile.persona.apellidos = 'General Inacap'
            admin_profile.persona.rut = '99.999.999-K'
            admin_profile.persona.save()
            admin_profile.reputation_score = 5.00
            admin_profile.is_verified_seller = True
            admin_profile.save()
            self.stdout.write(self.style.SUCCESS('Creado Administrador: admin@inacap.cl (Admin1234!)'))

        seller_user, created = UserCredential.objects.get_or_create(
            email='vendedor@inacap.cl',
            defaults={'role': UserCredential.ROLE_SELLER}
        )
        if created:
            seller_user.set_password('Vendedor1234!')
            seller_user.save()
            seller_profile = seller_user.user_profile
            seller_profile.public_alias = 'TechChile_Plaza'
            seller_profile.persona.nombres = 'Rodrigo'
            seller_profile.persona.apellidos = 'Morales Vendedor'
            seller_profile.persona.rut = '18.452.123-5'
            seller_profile.persona.save()
            seller_profile.reputation_score = 4.90
            seller_profile.is_verified_seller = True
            seller_profile.save()
            self.stdout.write(self.style.SUCCESS('Creado Vendedor: vendedor@inacap.cl (Vendedor1234!)'))
        else:
            seller_profile = seller_user.user_profile

        buyer_user, created = UserCredential.objects.get_or_create(
            email='comprador@inacap.cl',
            defaults={'role': UserCredential.ROLE_BUYER}
        )
        if created:
            buyer_user.set_password('Comprador1234!')
            buyer_user.save()
            buyer_profile = buyer_user.user_profile
            buyer_profile.public_alias = 'Cliente_Estudiante_Inacap'
            buyer_profile.persona.nombres = 'Valentina'
            buyer_profile.persona.apellidos = 'Pérez Estudiante'
            buyer_profile.persona.rut = '21.345.678-9'
            buyer_profile.persona.save()
            buyer_profile.save()
            self.stdout.write(self.style.SUCCESS('Creado Comprador: comprador@inacap.cl (Comprador1234!)'))

        # 3. Categorías
        cat_tech, _ = Category.objects.get_or_create(name='Tecnología & Celulares', defaults={'icon_name': 'Smartphone'})
        cat_comp, _ = Category.objects.get_or_create(name='Computación & Laptops', defaults={'icon_name': 'Laptop'})
        cat_audio, _ = Category.objects.get_or_create(name='Audio & Sonido', defaults={'icon_name': 'Headphones'})
        cat_moda, _ = Category.objects.get_or_create(name='Moda & Calzado', defaults={'icon_name': 'Shirt'})
        cat_hogar, _ = Category.objects.get_or_create(name='Hogar & Muebles', defaults={'icon_name': 'Home'})

        # 4. Productos con características ADS de más de 250 caracteres
        demo_products = [
            {
                'title': 'Samsung Galaxy S24 Ultra 256GB Titanium Gray',
                'description': 'Smartphone flagship con Galaxy AI integrado, cámara cuádruple de 200MP y procesador Snapdragon 8 Gen 3. Pantalla Dynamic AMOLED 2X de 6.8 pulgadas.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS OFICIALES: Procesador Snapdragon 8 Gen 3 for Galaxy de 4nm con IA integrada, pantalla Dynamic AMOLED 2X de 6.8 pulgadas QHD+ a 120Hz adaptativos con brillo pico de 2600 nits. Sistema de cámara cuádruple pro-grade con sensor principal de 200MP f/1.7 OIS, teleobjetivo periscópico de 50MP con zoom óptico 5x y Space Zoom hasta 100x. Batería inteligente de 5000 mAh con carga súper rápida de 45W. Chasis de titanio de grado aeroespacial resistente a caídas y certificación IP68.',
                'price': 1149990.00,
                'original_price': 1399990.00,
                'stock': 14,
                'category': cat_tech,
                'image_url': 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 12,
                'rating': 4.9,
                'reviews_count': 148,
            },
            {
                'title': 'Apple MacBook Pro 14 M3 Pro 18GB RAM 512GB SSD',
                'description': 'Laptop profesional de alto rendimiento con chip M3 Pro de Apple, pantalla Liquid Retina XDR de 14.2 pulgadas y hasta 18 horas de autonomía.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS PROFESIONALES: Equipado con el revolucionario procesador Apple M3 Pro con CPU de 11 núcleos y GPU de 14 núcleos con trazado de rayos acelerado por hardware. Memoria unificada ultra rápida de 18GB y almacenamiento SSD PCIe NVMe de 512GB de lectura a 5000MB/s. Pantalla Liquid Retina XDR de 14.2 pulgadas con resolución nativa de 3024x1964 y tecnología ProMotion a 120Hz. Puertos Thunderbolt 4, HDMI 2.1, ranura SDXC y conector de carga MagSafe 3.',
                'price': 2099990.00,
                'original_price': 2399990.00,
                'stock': 8,
                'category': cat_comp,
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 12,
                'rating': 5.0,
                'reviews_count': 92,
            },
            {
                'title': 'Audífonos Sony WH-1000XM5 Cancelación de Ruido Activa',
                'description': 'Líder en cancelación de ruido con dos procesadores y ocho micrófonos. Calidad de audio Hi-Res inalámbrico y llamadas ultra nítidas.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS AUDIO FILO: Cancelación activa de ruido Noise Cancelling líder en el mercado gracias a la combinación del procesador integrado V1 y el procesador de cancelación de ruido HD QN1. Ocho micrófonos de alta sensibilidad con tecnología Auto NC Optimizer y Precise Voice Pickup. Controladores de 30mm diseñados con precisión y cúpula de fibra de carbono. Compatibilidad con códecs LDAC Hi-Res Audio Wireless, DSEE Extreme y 30 horas de reproducción continua.',
                'price': 299990.00,
                'original_price': 389990.00,
                'stock': 25,
                'category': cat_audio,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.8,
                'reviews_count': 310,
            },
            {
                'title': 'Zapatillas Urbanas Nike Air Jordan 1 Retro High',
                'description': 'Diseño legendario con cuero genuino premium, amortiguación Air-Sole encapsulada y estilo atemporal para el día a día.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS CALZADO: Confeccionadas con una combinación de cuero flor genuino premium y capas superpuestas de gamuza de alta resistencia al desgaste. Unidad Air-Sole encapsulada en el talón para una amortiguación reactiva y protección contra impactos en cada pisada. Suela de goma sólida con punto de pivote circular que brinda máxima tracción multidireccional en pavimento urbano. Plantilla ergonómica acolchada con tratamiento antimicrobiano.',
                'price': 149990.00,
                'original_price': 189990.00,
                'stock': 19,
                'category': cat_moda,
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.7,
                'reviews_count': 64,
            },
            {
                'title': 'Smartwatch Garmin Forerunner 265 GPS AMOLED',
                'description': 'Reloj deportivo inteligente con pantalla táctil AMOLED de colores vibrantes, métricas de entrenamiento avanzadas y hasta 13 días de batería.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS DEPORTE: Pantalla táctil brillante AMOLED de 1.3 pulgadas protegida por cristal Corning Gorilla Glass 3. GPS multibanda de alta precisión con tecnología SatIQ que optimiza la recepción satelital y el consumo de batería. Sensor óptico de frecuencia cardíaca Elevate Gen 4 con pulsioxímetro Pulse Ox, cálculo de VO2 Max, estado de entrenamiento, predisposición y widget de carrera. Autonomía de hasta 13 días en modo smartwatch y 20 horas en modo GPS continuo.',
                'price': 389990.00,
                'original_price': 449990.00,
                'stock': 11,
                'category': cat_tech,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.9,
                'reviews_count': 53,
            },
            {
                'title': 'Silla Ergonómica de Oficina Herman Miller Style Black',
                'description': 'Soporte lumbar dinámico ajustable, reposabrazos 3D y malla transpirable de alta resistencia ideal para largas jornadas de trabajo o estudio.',
                'caracteristicas_ads': 'ESPECIFICACIONES ADS CONFORT: Estructura de ingeniería ergonómica con respaldo en malla técnica transpirable Pellicle que distribuye la presión de manera uniforme y evita la acumulación de calor corporal. Soporte lumbar dual PostureFit SL ajustable en profundidad y altura. Mecanismo de reclinación sincrónica con 4 posiciones de bloqueo y control de tensión. Reposabrazos 3D regulables en altura, ángulo y profundidad. Pistón de gas clase 4 certificado BIFMA.',
                'price': 219990.00,
                'original_price': 289990.00,
                'stock': 7,
                'category': cat_hogar,
                'image_url': 'https://images.unsplash.com/photo-1580481077195-c3f99506d128?w=900&auto=format&fit=crop&q=80',
                'free_shipping': True,
                'installments': 6,
                'rating': 4.6,
                'reviews_count': 29,
            }
        ]

        for p_data in demo_products:
            Product.objects.update_or_create(
                title=p_data['title'],
                defaults={
                    'seller_profile': seller_profile,
                    **p_data
                }
            )
            self.stdout.write(f"Producto cargado: {p_data['title']}")

        self.stdout.write(self.style.SUCCESS('Base de datos inicializada con éxito!'))
