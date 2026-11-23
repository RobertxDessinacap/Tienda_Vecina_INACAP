import uuid
from urllib.parse import urlencode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.payments.models import Order, OrderItem
from apps.payments.services import calculate_safe_cart_totals, TransbankWebpayService
from apps.products.models import Product


def _extract_validation_message(exc):
    if hasattr(exc, 'messages') and exc.messages:
        return str(exc.messages[0])
    if hasattr(exc, 'message'):
        return str(exc.message)
    return str(exc)


class CartCalculateAPIView(APIView):
    """
    Cálculo de carrito seguro en Backend (Anti-Manipulación JS).
    Recibe la lista de IDs y cantidades y computa los precios reales desde la DB.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {"status": "fail", "message": "El cuerpo de la solicitud debe ser un objeto JSON válido."},
                status=status.HTTP_400_BAD_REQUEST
            )
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
            return Response(
                {"status": "fail", "message": _extract_validation_message(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransbankInitAPIView(APIView):
    """
    Paso 1 Transbank Webpay Plus:
    Genera la orden con montos calculados en servidor e inicializa transacción con Transbank SDK.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {"status": "fail", "message": "El cuerpo de la solicitud debe ser un objeto JSON válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        raw_items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'WEBPAY_PLUS')
        valid_methods = {choice[0] for choice in Order.PAYMENT_METHOD_CHOICES}
        if payment_method not in valid_methods:
            return Response(
                {"status": "fail", "message": "Método de pago no soportado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            calculation = calculate_safe_cart_totals(raw_items)
        except ValidationError as e:
            return Response(
                {"status": "fail", "message": _extract_validation_message(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generar identificadores únicos de auditoría
        buy_order = f"OC-{uuid.uuid4().hex[:8].upper()}"
        session_id = f"SESS-{uuid.uuid4().hex[:12]}"
        total_amount = calculation['total']

        # Determinar UserProfile comprador si está autenticado
        buyer_profile = None
        if request.user and request.user.is_authenticated and hasattr(request.user, 'user_profile'):
            buyer_profile = request.user.user_profile

        # Iniciar transacción con Transbank SDK antes de persistir la orden (Fail-Closed)
        return_url = request.build_absolute_uri('/api/v1/payments/transbank/commit/')
        tbk_service = TransbankWebpayService()
        tbk_response = tbk_service.init_transaction(
            buy_order=buy_order,
            session_id=session_id,
            amount=int(total_amount),
            return_url=return_url
        )

        if tbk_response.get('status') != 'SUCCESS' or not tbk_response.get('token') or not tbk_response.get('url'):
            return Response(
                {
                    "status": "fail",
                    "message": "No fue posible iniciar el pago con Transbank Webpay Plus."
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        with transaction.atomic():
            order = Order.objects.create(
                buy_order=buy_order,
                session_id=session_id,
                buyer_profile=buyer_profile,
                total_amount=total_amount,
                payment_method=payment_method,
                status='INITIALIZED',
                transbank_token=tbk_response['token']
            )

            for item_data in calculation['items']:
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    unit_price=item_data['unit_price'],
                    quantity=item_data['quantity'],
                    subtotal=item_data['subtotal']
                )

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
    Soporta retorno por navegador (GET/form POST desde Webpay) y llamadas JSON API.
    Protegido contra bypass, replay y condiciones de carrera (select_for_update + F()).
    """
    permission_classes = [permissions.AllowAny]

    def _is_browser_redirect(self, request):
        if request.method == 'GET':
            return True
        content_type = (request.content_type or '').lower()
        if 'application/x-www-form-urlencoded' in content_type:
            return True
        accept = (request.META.get('HTTP_ACCEPT') or '').lower()
        if 'application/json' not in content_type and 'text/html' in accept:
            return True
        return False

    def _frontend_redirect(self, payment_status, buy_order='', **extra_params):
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        params = {'payment_status': payment_status}
        if buy_order:
            params['buy_order'] = buy_order
        for key, value in extra_params.items():
            if value not in (None, ''):
                params[key] = value
        return redirect(f"{base_url}/?{urlencode(params)}")

    def get(self, request):
        return self._handle_commit(request)

    def post(self, request):
        return self._handle_commit(request)

    def _handle_commit(self, request):
        is_browser = self._is_browser_redirect(request)
        data = request.data if isinstance(request.data, dict) or hasattr(request.data, 'get') else {}

        token_ws = (
            data.get('token')
            or data.get('token_ws')
            or request.query_params.get('token_ws')
        )
        tbk_token = (
            data.get('TBK_TOKEN')
            or request.query_params.get('TBK_TOKEN')
        )
        tbk_buy_order = (
            data.get('TBK_ORDEN_COMPRA')
            or request.query_params.get('TBK_ORDEN_COMPRA')
        )

        # Flujo abortado / cancelado en formulario Webpay (TBK_TOKEN sin token_ws)
        if tbk_token and not token_ws:
            buy_order = ''
            with transaction.atomic():
                order = Order.objects.select_for_update().filter(transbank_token=tbk_token).first()
                if order:
                    buy_order = order.buy_order
                    if order.status == 'INITIALIZED':
                        order.status = 'FAILED'
                        order.save(update_fields=['status', 'updated_at'])
            if is_browser:
                return self._frontend_redirect('CANCELLED', buy_order=buy_order)
            return Response(
                {"status": "fail", "message": "La transacción fue cancelada por el usuario en Transbank."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tbk_buy_order and not token_ws:
            with transaction.atomic():
                order = Order.objects.select_for_update().filter(buy_order=tbk_buy_order).first()
                if order and order.status == 'INITIALIZED':
                    order.status = 'FAILED'
                    order.save(update_fields=['status', 'updated_at'])
            if is_browser:
                return self._frontend_redirect('CANCELLED', buy_order=tbk_buy_order)
            return Response(
                {"status": "fail", "message": "La transacción expiró o fue cancelada en Transbank."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not token_ws:
            if is_browser:
                return self._frontend_redirect('ERROR')
            return Response(
                {"status": "fail", "message": "Token de Transbank no suministrado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        tbk_service = TransbankWebpayService()

        with transaction.atomic():
            order = Order.objects.select_for_update().filter(transbank_token=token_ws).first()
            if not order:
                if is_browser:
                    return self._frontend_redirect('NOT_FOUND')
                return Response(
                    {"status": "fail", "message": "No se encontró orden asociada al token de pago."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Protección de Idempotencia / Replay: no volver a llamar a Transbank ni descontar stock
            if order.status != 'INITIALIZED':
                if is_browser:
                    return self._frontend_redirect(order.status, buy_order=order.buy_order)
                return Response(
                    {"status": "fail", "message": "Esta orden ya fue procesada y finalizada previamente."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Bloqueo determinista de filas de producto en orden ascendente de ID
            items = list(order.items.select_related('product').order_by('product_id'))
            product_ids = [item.product_id for item in items]
            locked_products = {
                p.id: p
                for p in Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
            }

            commit_result = tbk_service.commit_transaction(token_ws)

            committed_amount = commit_result.get('amount')
            amount_matches = True
            if committed_amount is not None:
                try:
                    amount_matches = int(round(float(committed_amount))) == int(round(float(order.total_amount)))
                except (ValueError, TypeError):
                    amount_matches = False

            if commit_result.get('status') != 'AUTHORIZED' or not amount_matches:
                order.status = 'FAILED'
                order.save(update_fields=['status', 'updated_at'])
                if is_browser:
                    return self._frontend_redirect('FAILED', buy_order=order.buy_order)
                return Response({
                    "status": "fail",
                    "message": "La transacción fue rechazada por Transbank o cancelada por el usuario.",
                    "status_code": commit_result.get('response_code')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verificar suficiencia de stock en todos los productos bloqueados antes de descontar
            required_qty_by_product = {}
            for item in items:
                required_qty_by_product[item.product_id] = (
                    required_qty_by_product.get(item.product_id, 0) + item.quantity
                )

            has_all_stock = bool(items) and all(
                pid in locked_products and locked_products[pid].stock >= qty
                for pid, qty in required_qty_by_product.items()
            )

            if not has_all_stock:
                tbk_service.refund_transaction(token_ws, int(round(float(order.total_amount))))
                order.status = 'REVERSED'
                order.save(update_fields=['status', 'updated_at'])
                if is_browser:
                    return self._frontend_redirect('REVERSED', buy_order=order.buy_order)
                return Response({
                    "status": "fail",
                    "message": "Stock insuficiente al confirmar el pago. La transacción fue reversada automáticamente."
                }, status=status.HTTP_409_CONFLICT)

            # Descuento atómico todo-o-nada con savepoint
            sid = transaction.savepoint()
            for item in items:
                updated = Product.objects.filter(
                    id=item.product_id,
                    stock__gte=item.quantity
                ).update(stock=F('stock') - item.quantity)
                if not updated:
                    transaction.savepoint_rollback(sid)
                    tbk_service.refund_transaction(token_ws, int(round(float(order.total_amount))))
                    order.status = 'REVERSED'
                    order.save(update_fields=['status', 'updated_at'])
                    if is_browser:
                        return self._frontend_redirect('REVERSED', buy_order=order.buy_order)
                    return Response({
                        "status": "fail",
                        "message": "Stock insuficiente al confirmar el pago. La transacción fue reversada automáticamente."
                    }, status=status.HTTP_409_CONFLICT)
            transaction.savepoint_commit(sid)

            order.status = 'AUTHORIZED'
            order.authorization_code = commit_result.get('authorization_code')
            order.card_last_digits = commit_result.get('card_number')
            order.payment_type_code = commit_result.get('payment_type_code')
            shares_number = commit_result.get('shares_number')
            order.shares_number = 1 if shares_number is None else shares_number
            order.save()

        if is_browser:
            return self._frontend_redirect(
                'AUTHORIZED',
                buy_order=order.buy_order,
                auth_code=order.authorization_code or '',
                amount=int(round(float(order.total_amount))),
                card_last_digits=order.card_last_digits or '',
            )

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
