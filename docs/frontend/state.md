# Gestión de Estado

El estado del frontend se organiza en tres capas según su ámbito y ciclo de vida: autenticación global, datos de analítica y navegación por pestañas.

---

## Resumen de capas

| Capa | Mecanismo | Ámbito | Persistencia |
|---|---|---|---|
| Autenticación global | React Context (`AuthContext`) | Toda la app | Cookie `auth_token` (24 h) |
| Datos de analítica | `useReducer` (`analyticsReducer`) | Página `/analytics` | Memoria (pestaña actual) |
| Pestaña activa | URL query param `?tab=N` | Página `/analytics` | URL (enlazable) |

---

## `AuthContext` y persistencia con cookies

El token JWT se almacena en una cookie HTTP (`auth_token`, 24 h), no en `localStorage`.
La razón es arquitectónica ya que `middleware.ts` corre en el Edge Runtime antes de que el
navegador reciba ningún HTML y puede leer cookies, pero no `localStorage`. Esto permite
verificar la autenticación y redirigir a `/login` sin renderizar ningún fotograma de la página protegida.

La interfaz del contexto, las funciones de cookie y el comportamiento por situación están
documentados en [Hooks y Contexto](hooks.md#authcontext).

---

## `useReducer` para analítica

**Archivo:** `frontend/src/hooks/useFetchTab.ts` (reducer + estado inicial)  
**Consumidor:** `frontend/src/app/analytics/page.tsx`

Para evitar la fragmentación a través de múltiples variables de estado independientes,
la página `/analytics` consolida la orquestación de las siete pestañas en un único árbol
de estado (`AnalyticsState`). La lógica de actualización se delega a un *reducer* puro
definido en `useFetchTab.ts`, y el ciclo de vida es estrictamente unidireccional, por lo que 
cuando el *hook* resuelve la petición de una pestaña, emite una acción que integra el nuevo
*payload* de forma inmutable, actualizando exclusivamente los *slices* correspondientes
y preservando intacta la caché de las pestañas previamente visitadas.

### Forma del estado (`AnalyticsState`)

```typescript
type AnalyticsState = {
  // Tab 0 - Contratos
  contracts:      ContractProfileData | null;
  contractDetail: ContractDetailRow[];
  // Tab 1 - Riesgo
  risk:           RiskData | null;
  scores:         SupplierScoreRow[];
  fragility:      BuyerFragilityRow[];
  geographic:     GeographicRiskRow[];
  // Tab 2 - Discrepancias
  discrepancy:    DiscrepancyRow[];
  commercial:     CommercialImpactRow[];
  // Tab 3 - Lead Time
  leadTime:       LeadTimeRow[];
  // Tab 4 - Exposición
  payment:        PaymentRow[];
  overdueRows:    OverdueRow[];
  // Tab 5 - Trazabilidad
  lineage:        LineageRow[];
  exactPaths:     ExactPathRow[];
  forward:        ForwardRow[];
  // Tab 6 - GDS
  gds:            GdsData;
};
```

### Acciones disponibles

| Acción | Slices actualizados | Endpoints |
|---|---|---|
| `SET_CONTRACTS` | `contracts`, `contractDetail` | `/api/analytics/risk/contracts`, `/api/analytics/risk/contracts-detail` |
| `SET_RISK` | `risk`, `scores`, `fragility`, `geographic` | `/api/analytics/risk`, `/api/analytics/risk/supplier-score`, `/api/analytics/risk/buyer-fragility`, `/api/analytics/risk/geographic` |
| `SET_DISCREPANCY` | `discrepancy`, `commercial` | `/api/analytics/discrepancy-suppliers`, `/api/analytics/risk/commercial-impact` |
| `SET_LEAD_TIME` | `leadTime` | `/api/analytics/lead-time` |
| `SET_EXPOSURE` | `payment`, `overdueRows` | `/api/analytics/payment`, `/api/analytics/risk/overdue` |
| `SET_TRACEABILITY` | `lineage`, `exactPaths`, `forward` | `/api/analytics/lineage/backward`, `/api/analytics/lineage/exact-paths`, `/api/analytics/lineage/forward` |
| `SET_GDS` | `gds` | `/api/analytics/gds` |

---

## URL State y Deep Linking

El estado de la pestaña activa no se retiene en la memoria local del componente, 
sino que se delega estructuralmente al parámetro de consulta `?tab=N` de la URL. 
Esta decisión arquitectónica habilita el *deep linking* (permitiendo compartir accesos 
directos como `/analytics?tab=5` hacia Trazabilidad) e integra la navegación entre pestañas 
de forma nativa con el historial del navegador.

```typescript
// Lectura con validación de bounds
const rawTab    = parseInt(searchParams.get("tab") ?? "0", 10);
const activeTab = isNaN(rawTab) || rawTab < 0 || rawTab > 6 ? 0 : rawTab;

// Escritura (al hacer clic en un tab)
router.push(`/analytics?tab=${index}`);
```

Para garantizar la robustez, la lectura del parámetro incorpora una capa de sanitización 
defensiva donde cualquier valor no numérico o fuera del rango válido (0–6) fuerza un fallback 
a la pestaña de Contratos (0). El `Sidebar` adopta estas URLs como única fuente de verdad, 
construyendo sus enlaces directamente sobre este formato para garantizar la sincronía 
absoluta entre la navegación lateral y el contenido en pantalla.

### `Suspense` boundary

La integración del hook `useSearchParams` en la arquitectura App Router impone una restricción 
de diseño donde el componente lector debe estar envuelto en un límite de renderizado asíncrono. 
Por este motivo, el módulo se divide en dos capas de responsabilidad:

- `AnalyticsContent`: El núcleo lógico que lee la URL, orquesta el estado global y renderiza la interfaz.
- `AnalyticsPage` (Default Export): El componente contenedor que aísla al núcleo dentro de
  `<Suspense fallback={<LoadingState />}>`. Esto previene fallos de compilación estática durante el build 
  y garantiza una transición suave en la UI durante la resolución inicial de la URL.