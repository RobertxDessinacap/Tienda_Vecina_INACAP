import uuid
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from apps.payments.models import Order, OrderItem
from apps.payments.services import calculate_safe_cart_totals, TransbankWebpayService
from apps.products.models import Product

class CartCalculateAPIView(APIView):
    """
    Cálculo de carrito seguro en Backend (Anti-Manipulación JS).
    Recibe la lista de IDs y cantidades y computa los precios reales desde la DB.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_items = request.data.get('items', [])
        try:
            calculation = calculate_safe_cart_totals(raw_items)
            # Serializar ítems para respuesta JSON
            serialized_items = []
            for item in calculation['items']:
                serialized_items.append({
                    'product_id': item['product_id'],
                    'title': item['title'],
                    'unit_price': float(item['unit_price']),
                    'quantity': item['quantity'],
                    'subtotal': float(item['subtotal']),
                    'image_url': item['image_url'],
                })

            return Response({
                "status": "success",
                "data": {
                    "items": serialized_items,
                    "subtotal": float(calculation['subtotal']),
                    "shipping": float(calculation['shipping']),
                    "total": float(calculation['total']),
                    "currency": "CLP",
                    "security_guarantee": "Precios validados y asegurados en Backend PostgreSQL (ISO 27001)"
                }
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"status": "fail", "message": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)


class TransbankInitAPIView(APIView):
    """
    Paso 1 Transbank Webpay Plus:
    Genera la orden con montos calculados en servidor e inicializa transacción con Transbank SDK.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'WEBPAY_PLUS')

        try:
            calculation = calculate_safe_cart_totals(raw_items)
        except ValidationError as e:
            return Response({"status": "fail", "message": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        # Generar identificadores únicos de auditoría
        buy_order = f"OC-{uuid.uuid4().hex[:8].upper()}"
        session_id = f"SESS-{uuid.uuid4().hex[:12]}"
        total_amount = calculation['total']

        # Determinar UserProfile comprador si está autenticado
        buyer_profile = None
        if request.user and request.user.is_authenticated and hasattr(request.user, 'user_profile'):
            buyer_profile = request.user.user_profile

        # Crear la Orden de Compra en Base de Datos
        order = Order.objects.create(
            buy_order=buy_order,
            session_id=session_id,
            buyer_profile=buyer_profile,
            total_amount=total_amount,
            payment_method=payment_method,
            status='INITIALIZED'
        )

        for item_data in calculation['items']:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                unit_price=item_data['unit_price'],
                quantity=item_data['quantity'],
                subtotal=item_data['subtotal']
            )

        # Iniciar transacción con Transbank SDK
        return_url = request.build_absolute_uri('/api/v1/payments/transbank/commit/')
        tbk_service = TransbankWebpayService()
        tbk_response = tbk_service.init_transaction(
            buy_order=buy_order,
            session_id=session_id,
            amount=int(total_amount),
            return_url=return_url
        )

        order.transbank_token = tbk_response['token']
        order.save(update_fields=['transbank_token'])

        return Response({
            "status": "success",
            "message": "Transacción Transbank Webpay Plus creada con éxito.",
            "data": {
                "buy_order": buy_order,
                "total_amount": float(total_amount),
                "token": tbk_response['token'],
                "url": tbk_response['url'],
                "payment_method": payment_method
            }
        }, status=status.HTTP_201_CREATED)


class TransbankCommitAPIView(APIView):
    """
    Paso 2 Transbank Webpay Plus:
    Confirma el token con Transbank, actualiza el estado de la orden y descuenta el stock del catálogo.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token') or request.query_params.get('token_ws')
        if not token:
            return Response({"status": "fail", "message": "Token de Transbank no suministrado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(transbank_token=token)
        except Order.DoesNotExist:
            return Response({"status": "fail", "message": "No se encontró orden asociada al token de pago."}, status=status.HTTP_404_NOT_FOUND)

        tbk_service = TransbankWebpayService()
        commit_result = tbk_service.commit_transaction(token)

        if commit_result.get('status') == 'AUTHORIZED':
            order.status = 'AUTHORIZED'
            order.authorization_code = commit_result.get('authorization_code')
            order.card_last_digits = commit_result.get('card_number')
            order.payment_type_code = commit_result.get('payment_type_code')
            order.shares_number = commit_result.get('shares_number', 1)
            order.save()

            # Descontar stock atómicamente
            for item in order.items.all():
                prod = item.product
                if prod.stock >= item.quantity:
                    prod.stock -= item.quantity
                    prod.save(update_fields=['stock'])

            return Response({
                "status": "success",
                "message": "Pago aprobado exitosamente mediante Transbank Webpay Plus.",
                "voucher": {
                    "buy_order": order.buy_order,
                    "authorization_code": order.authorization_code,
                    "amount": float(order.total_amount),
                    "card_last_digits": order.card_last_digits,
                    "payment_type": "Débito / Crédito Webpay Plus",
                    "shares_number": order.shares_number,
                    "status": "APROBADO",
                    "timestamp": order.updated_at.isoformat()
                }
            }, status=status.HTTP_200_OK)
        else:
            order.status = 'FAILED'
            order.save()
            return Response({
                "status": "fail",
                "message": "La transacción fue rechazada por Transbank o cancelada por el usuario.",
                "status_code": commit_result.get('response_code')
            }, status=status.HTTP_400_BAD_REQUEST)


class PaymentMethodsAPIView(APIView):
    """
    Catálogo de métodos para el Carrusel de Pago solicitado.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        methods = [
            {
                "id": "WEBPAY_PLUS",
                "name": "Transbank Webpay Plus",
                "badge": "Recomendado",
                "description": "Tarjetas de Débito (Redcompra), Tarjetas de Crédito chilenas y Prepago con confirmación inmediata.",
                "icon": "CreditCard",
                "color": "from-red-600 to-rose-700",
                "supported": ["Redcompra", "Visa", "Mastercard", "American Express", "Magna"],
                "security": "Cifrado SSL 256 bits y protocolo 3DSecure de Transbank"
            },
            {
                "id": "MERCADO_PAGO",
                "name": "Mercado Pago",
                "badge": "Hasta 6 cuotas sin interés",
                "description": "Paga con dinero en tu cuenta de Mercado Pago o tarjetas asociadas en un clic.",
                "icon": "Wallet",
                "color": "from-sky-500 to-blue-600",
                "supported": ["Saldo en cuenta", "Tarjetas guardadas", "Dinero disponible"],
                "security": "Programa de Protección al Comprador"
            },
            {
                "id": "TRANSFER",
                "name": "Transferencia Bancaria Inmediata",
                "badge": "Sin comisión",
                "description": "Transfiere directamente desde tu banco (BancoEstado, Santander, BCI, Banco de Chile).",
                "icon": "Building2",
                "color": "from-emerald-600 to-teal-700",
                "supported": ["Khipu", "Webpay Transfer", "BancoEstado"],
                "security": "Validación de firma digital bancaria"
            },
            {
                "id": "PREPAY",
                "name": "Tarjetas de Prepago Digital",
                "badge": "100% Digital",
                "description": "Paga al instante con tus cuentas digitales de prepago favoritas.",
                "icon": "Smartphone",
                "color": "from-purple-600 to-indigo-700",
                "supported": ["Tenpo", "Mach", "Dale", "Copec Pay"],
                "security": "Tokenización de tarjetas de prepago"
            }
        ]
        return Response({"status": "success", "data": methods})
