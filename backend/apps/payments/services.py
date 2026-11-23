import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.products.models import Product
from apps.payments.models import Order, OrderItem

logger = logging.getLogger(__name__)

# Transbank Webpay Plus SDK Oficial
try:
    from transbank.webpay.webpay_plus.transaction import Transaction
    from transbank.common.integration_type import IntegrationType
    from transbank.common.options import WebpayOptions
    HAS_TRANSBANK_SDK = True
except ImportError:
    HAS_TRANSBANK_SDK = False


def calculate_safe_cart_totals(raw_items):
    """
    Seguridad Crítica (Requisito del Profesor):
    'Los procesos donde tenga información delicada no deben estar generadas, calculadas o analizadas por JS'.
    Los precios se extraen DIRECTAMENTE desde la base de datos PostgreSQL/ORM.
    Cualquier precio o total enviado por el frontend en JavaScript es completamente ignorado.
    """
    if not raw_items or not isinstance(raw_items, list):
        raise ValidationError("El carrito de compras no contiene productos válidos.")

    aggregated_quantities = {}

    for item in raw_items:
        if not isinstance(item, dict):
            raise ValidationError("Cada ítem del carrito debe ser un objeto válido.")

        prod_id = item.get('product_id') or item.get('id')
        if not prod_id or isinstance(prod_id, bool):
            raise ValidationError("Identificador de producto faltante o inválido.")

        try:
            prod_uuid = uuid.UUID(str(prod_id))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError(f"Identificador de producto '{prod_id}' no es un UUID válido.")

        raw_qty = item.get('quantity', 1)
        if isinstance(raw_qty, bool) or (isinstance(raw_qty, float) and not raw_qty.is_integer()):
            raise ValidationError(
                f"La cantidad proporcionada para el producto '{prod_id}' no es un número entero válido."
            )

        try:
            qty = int(raw_qty)
        except (ValueError, TypeError, OverflowError):
            raise ValidationError(
                f"La cantidad proporcionada para el producto '{prod_id}' no es un número entero válido."
            )

        if qty <= 0:
            raise ValidationError("La cantidad debe ser un entero mayor o igual a 1.")

        aggregated_quantities[prod_uuid] = aggregated_quantities.get(prod_uuid, 0) + qty

    if not aggregated_quantities:
        raise ValidationError("El carrito está vacío.")

    verified_items = []
    total_amount = Decimal('0.00')

    for prod_uuid, total_requested_qty in aggregated_quantities.items():
        try:
            product = Product.objects.get(id=prod_uuid)
        except Product.DoesNotExist:
            raise ValidationError(f"Producto con identificador '{prod_uuid}' no encontrado en catálogo.")

        if product.stock < total_requested_qty:
            raise ValidationError(
                f"Stock insuficiente para '{product.title}'. Solicitado: {total_requested_qty}, Disponible: {product.stock}"
            )

        # Precio real e inmutable tomado de la base de datos
        db_price = product.price
        subtotal = db_price * total_requested_qty
        total_amount += subtotal

        verified_items.append({
            'product': product,
            'product_id': str(product.id),
            'title': product.title,
            'unit_price': db_price,
            'quantity': total_requested_qty,
            'subtotal': subtotal,
            'image_url': product.display_image_url
        })

    return {
        'items': verified_items,
        'subtotal': total_amount,
        'shipping': Decimal('0.00'),  # Envío gratis estándar
        'total': total_amount
    }


class TransbankWebpayService:
    """
    Servicio de Integración con Transbank Webpay Plus (Fail-Closed).
    Soporta IntegrationType.LIVE y IntegrationType.TEST según TRANSBANK_ENVIRONMENT.
    """
    def __init__(self):
        self.commerce_code = settings.TRANSBANK_COMMERCE_CODE
        self.api_key = settings.TRANSBANK_API_KEY
        self.environment = settings.TRANSBANK_ENVIRONMENT

    def get_tx(self):
        if not HAS_TRANSBANK_SDK:
            return None
        env_str = str(self.environment or '').strip().upper()
        integration_type = (
            IntegrationType.LIVE
            if env_str in ('LIVE', 'PRODUCCION', 'PRODUCTION')
            else IntegrationType.TEST
        )
        options = WebpayOptions(self.commerce_code, self.api_key, integration_type)
        return Transaction(options)

    def init_transaction(self, buy_order: str, session_id: str, amount: int, return_url: str):
        """Paso 1 Transbank: Crea la transacción en Webpay Plus (Fail-Closed)."""
        tx = self.get_tx()
        if not tx:
            return {
                'status': 'ERROR',
                'error': 'SDK de Transbank no disponible.'
            }

        try:
            response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=int(amount),
                return_url=return_url
            )
            token = response.get('token') if isinstance(response, dict) else getattr(response, 'token', None)
            url = response.get('url') if isinstance(response, dict) else getattr(response, 'url', None)
            if not token or not url:
                logger.error("Transbank init_transaction: respuesta sin token o url para orden %s", buy_order)
                return {
                    'status': 'ERROR',
                    'error': 'Respuesta incompleta de Transbank al iniciar transacción.'
                }
            return {
                'token': token,
                'url': url,
                'status': 'SUCCESS'
            }
        except Exception as e:
            logger.error("Transbank init_transaction falló para orden %s: %s", buy_order, type(e).__name__)
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    def commit_transaction(self, token: str):
        """Paso 2 Transbank: Confirma la transacción con verificación estricta (Fail-Closed)."""
        tx = self.get_tx()
        if not tx or not token or str(token).startswith('tbk_token_'):
            return {
                'status': 'REJECTED',
                'response_code': -1,
                'error': 'Token inválido o pasarela no disponible.'
            }

        try:
            response = tx.commit(token)
            resp_dict = response if isinstance(response, dict) else response.__dict__
            card_detail = resp_dict.get('card_detail') or {}
            if not isinstance(card_detail, dict):
                card_detail = getattr(card_detail, '__dict__', {}) or {}

            response_code = resp_dict.get('response_code')
            is_approved = (response_code == 0)
            shares_number = resp_dict.get('shares_number')

            return {
                'response_code': response_code,
                'authorization_code': resp_dict.get('authorization_code'),
                'amount': resp_dict.get('amount'),
                'card_number': card_detail.get('card_number') or '0000',
                'payment_type_code': resp_dict.get('payment_type_code') or 'VN',
                'shares_number': 1 if shares_number is None else shares_number,
                'status': 'AUTHORIZED' if is_approved else 'REJECTED'
            }
        except Exception as e:
            logger.error("Transbank commit_transaction falló: %s", type(e).__name__)
            return {
                'status': 'REJECTED',
                'response_code': -1,
                'error': str(e)
            }

    def refund_transaction(self, token: str, amount: int):
        """Reversa o anula una transacción previamente confirmada en Webpay Plus."""
        tx = self.get_tx()
        if not tx or not token or str(token).startswith('tbk_token_'):
            return {
                'status': 'ERROR',
                'error': 'Token inválido o pasarela no disponible.'
            }

        try:
            response = tx.refund(token, int(amount))
            resp_dict = response if isinstance(response, dict) else getattr(response, '__dict__', {})
            return {
                'status': 'REVERSED',
                'type': resp_dict.get('type'),
                'authorization_code': resp_dict.get('authorization_code'),
                'response_code': resp_dict.get('response_code'),
                'nullified_amount': resp_dict.get('nullified_amount'),
                'balance': resp_dict.get('balance'),
            }
        except Exception as e:
            logger.error("Transbank refund_transaction falló: %s", type(e).__name__)
            return {
                'status': 'ERROR',
                'error': str(e)
            }
