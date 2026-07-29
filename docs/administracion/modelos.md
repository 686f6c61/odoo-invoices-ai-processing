# Modelos y respaldo

## Catálogo

La sincronización conserva el historial. Un modelo que desaparece del servicio
se marca como no disponible; no se borra junto con sus intentos.

## Capacidad documental

Un modelo puede quedar:

| Estado | Interpretación |
|---|---|
| Sin verificar | No hay evidencia suficiente |
| Declarado por el servicio | El catálogo anuncia modalidad visual/documental |
| Sonda superada | Leyó correctamente la imagen de comprobación |
| Aprobado por administrador | Excepción manual con responsabilidad administrativa |
| Sonda fallida | No respondió como se esperaba |

Solo los modelos documentales disponibles pueden elegirse como principal o
respaldo.

## Elección del modelo principal

Valore con facturas representativas:

- exactitud de proveedor, conceptos e importes;
- lectura de escaneos y tablas;
- estabilidad del JSON;
- latencia;
- coste;
- ubicación y retención de datos;
- tamaño de contexto y límites de salida.

No elija únicamente por el nombre o el tamaño del modelo.

## Respaldo

El respaldo se utiliza ante:

- error temporal de red o proveedor;
- rechazo específico de la petición por el modelo;
- salida que no cumple el contrato estructurado.

No se utiliza para ocultar:

- una clave inválida;
- falta de permisos;
- ausencia de consentimiento;
- un archivo no admitido;
- un endpoint bloqueado por seguridad.

## Temperatura y tokens

Mantenga la temperatura en `0` para extracción determinista. El rango permitido
es de `0` a `2`.

Los tokens de salida admiten entre `256` y `32.768`. Aumente el valor solo si
las facturas con muchas líneas quedan truncadas. Más tokens no mejoran una
imagen ilegible y pueden aumentar coste y tiempo.

## Evaluación periódica

Compare principal y respaldo con un conjunto controlado de facturas. Registre
errores por campo y no cambie de modelo directamente en producción sin una
prueba de regresión.
