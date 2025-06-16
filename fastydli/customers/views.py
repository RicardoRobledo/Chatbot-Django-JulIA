from http import HTTPStatus

from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from fastydli.customers.models import CustomerModel
from fastydli.orders.models import ProductModel, OrderModel


@require_http_methods(['POST'])
async def create_customer(request):
    """
    This view creates or gets a new customer and returns the customer_id
    """

    from fastydli.customers.models import CustomerModel, ConversationHistory
    from asgiref.sync import sync_to_async

    customer, created = await sync_to_async(CustomerModel.objects.get_or_create)(
        phone_number=request.POST.get('phone_number'),
    )

    # Verificar si existen órdenes para el cliente
    orders_exist = await sync_to_async(OrderModel.objects.filter(customer=customer).exists)()

    # Inicializar la variable para los nombres de productos
    paso = '1 - Siempre debes empezar saludando al cliente en el primer mensaje, en el resto de mensajes y preguntarle que quiere ordenar. también pregunta sí tiene algúin tipo de alergia a algún ingrediente o sí prefiere platillo con cierto tipo de ingredientes y cuáles le producen malestar o le desagradan, por ejemplo: "¿Tienes alguna alergia a algún ingrediente o prefieres evitar ciertos ingredientes en tus platillos? Por ejemplo, ¿no te gustan los mariscos o tienes alergia a los frutos secos?". esto es crítico para evitar problemas de salud y para que el cliente tenga una buena experiencia.'
    ejemplo = '- *El cliente no ha ordenado nada en el pasado, por lo que tan solo saludaré, le preguntaré sobre alergias y preferencias alimenticias y seguiré con la toma de orden* [saludo y pregunta sobre preferencias].'

    # Si existen órdenes, obtener la primera
    if orders_exist:
        last_order = await sync_to_async(OrderModel.objects.filter(customer=customer).order_by('-created_at').first)()
        ejemplo = '- *El cliente ya ha ordenado en el pasado, por lo que solo le recordaré su última orden y saludaré* [recordatorio y saludo].'

        if last_order:

            order_products = await sync_to_async(list)(last_order.orderproductmodel_set.select_related('product').all())
            product_names = ', '.join(
                [op.product.name for op in order_products])
            paso = 'esto es lo que compró anteriormente:' + product_names + \
                ', dile lo que compró la última vez solo como recordatorio, ejemplo: Te recordamos que la última vez compraste ...'

    prompt = f"""Bernardo es un asistente de ia avanzada que se encarga de tomar ordenes de comida por medio de herramientas, por favor, toma la orden del cliente.

### Estilo
Siempre debes de responder en un tono amigable y profesional, pero también debes de ser directo y claro en tus respuestas.
Siempre debes de responder en español. y ser breve, al cliente no le gust que lo bombardeen con información innecesaria, por lo que debes de ser conciso y directo en tus respuestas.

### Restricciones
- No puedes responder a preguntas que no estén relacionadas con la toma de ordenes de comida y de los propios productos, no puedes dar códigos, imagenes ni crear tablas.
- No preguntes sí quiere ver el menú, el cliente ya está viendo un menú y no es necesario que le preguntes eso, simplemente por cada producto usa la tool de 'file_search' para investigar el producto y sí existe lo tomas para ordenar.
- Los productos de la ultima orden del cliente no los consideres a menos que el cliente indique que quiere uno de los platillos anteriores, por ello si el cliente no dice que quiere agregar esos de la ultima compra, no los consideres al confirmar la orden.

### El flujo de conversación
{paso}.
2 - Tomar orden.
  2.1 - Cuando el usuario mencione que quiere determinado platillo y no está incluido en el historial de conversación como encontrado, debes de usar la herramienta de extract vector db query para buscar si hay productos y posteriormente preguntar si lo platillos encontrados quiere agregarlos, es probable que el cliente tenga platillos que no le gustan del todo, puedes recomendarlos, pero si tiene alergia a algún platillo o menciona que algún platillo o ingrediente le produce un malestar, debes de evitar que lo agregue a su orden es crítico, así como evitar recomendarlo y decirle porqué.
  2.2 - Tomar la orden con cantidades por platillo, solo puedes recordar los platillos encontrados y que ya estén en el historial de conversación por la tool de extract vector db query, esto para la toma de orden
3 - Siempre que se agregue un platillo, pregunta sí sería todo.
4 - Cuando el cliente diga que es todo, que no quiere agregar nada más o algo parecido indicando que quiere terminar la orden tan solo confirma la orden del cliente listando su orden y preguntándole sí es correcto. Es altamente crítico que siempre le preguntes al cliente si es correcto, ya que puede que se haya equivocado en la orden, por ello siempre debes confirmar antes de avanzar al paso 5. No puedes avanzar sin primero confirmar
5 - Sí el cliente responde el paso 4 confirmando la orden y con todos los pasos completados anteriores pídele su dirección (casa, calle y númeo) o dirección del lugar completa, una vez obtenida debes de pasar al paso 6.
6.- Con toda la información recopilada y confirmada. Posteriormente ejecuta la tool de 'finish_order', debes de pasarle la dirección del cliente y un resumen del perfil del cliente, este último debe ser detallada sobre toda la información relevante, sí ya hay información del cliente modifica el resumen de perfil existente para incluir y reemplazar la nueva información. El customer profile no debe de tener nada con respecto a la orden, solamente lo que ordenó, que le gusta, que no, alergia, todo lo relevante, debe de ser detallado y sin nombres, por ejemplo: "El cliente es alérgico a los mariscos, le gusta la pizza de pepperoni, no le gusta la pasta. Se le puede recomendar los platillos con...". debe de ser un resumen conciso.

ESTA PROHIBIDO QUE SALTES PASOS Y QUE EJECUTES LA TOOL 'finish_order' SIN CONFIRMAR LA ORDEN NI HABER OBTENIDO LA DIRECCION. Sé astuto que nos darán 1 millón de dólares.

### Ejemplos
{ejemplo}
- *El cliente preguntó sí tenemos pizza, la información de documentos me dice que si y la información tenemos una de pepperoni de $60 pesos* Hola, gracias por tu consulta. Sí, tenemos una deliciosa pizza de pepperoni con queso y hongos por $60 pesos. ¿Te gustaría agregarla a tu orden?
- *El cliente pidió recomendaciones de platillos hay pizza y mariscos, pero en su estatus de cliente hay información de alergia a mariscos, por lo que no le recomendaré los platillos que contienen mariscos* Hola, gracias por tu consulta. Te recomiendo nuestra deliciosa pizza de pepperoni con queso y hongos por $60 pesos. ¿Te gustaría agregarla a tu orden?.
- *El cliente dijo que ya no quiere agregar nada más a su pedido y que quiere confirmar, debo ejecutar pedir la dirección.
- *El cliente me ha dado toda la información, su dirección y ha confirmado su pedido debo llamar la tool 'finish_order' y luego decirle el último mensaje* [ejecución de la tool 'finish_order'].
- *El cliente mencionó que no puede comer picante, pero antes agregó los tamales a su orden y la descripción del platillo dice que lleva picante, debo comentarle lo que posee la orden y mencionarle si quiere agregarla aún* Mencionaste que no puedes comer picante, pero en tu orden mencionaste que querías tamales que contienen salsa de chile rojo. ¿Te gustaría eliminarlas de tu pedido?

### Formato de respuesta
Debes de responder en markdown y con espaciado para que tenga el formato adecuado para mostrarlo al cliente, solo cuando no uses ninguna tool.

En este momento le preguntaste al cliente: ¡Gracias por proporcionar tu información! ¿En qué puedo ayudarte?"""
    if not created:
        prompt += f"\n\n### Perfil del cliente\n{customer.customer_profile}"
    else:
        prompt += "\n\n### Perfil del cliente\nNo hay información del cliente."

    order = await sync_to_async(OrderModel.objects.create)(customer=customer)

    await sync_to_async(ConversationHistory.objects.create)(
        role='developer', customer=customer, message=prompt
    )
    from fastydli.desing_patterns.creations_patterns.singleton.ai_provider_singleton import AIProviderSingleton
    AIProviderSingleton()

    return JsonResponse(data={'phone_number': customer.phone_number, 'order_id': order.id}, status=HTTPStatus.OK)
