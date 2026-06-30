# Inventario de Componentes

El ecosistema de presentación sigue una arquitectura basada en componentes (*Component-Driven Architecture*), 
organizada en seis espacios bajo el directorio `frontend/src/components/`. 

El diseño obedece estrictamente al Principio de Responsabilidad Única (SRP) en el que 
los módulos visuales (`charts/`, `ui/`) encapsulan la lógica de renderizado estético, 
mientras que los módulos de dominio (`analytics/`, `dashboard/`) actúan como orquestadores de las vistas. 
Para garantizar un flujo de datos unidireccional y predecible, los componentes de presentación 
operan como funciones puras sin efectos secundarios de red por lo que la inyección de datos es 
exclusivamente mediante *props* delegadas por los controladores de cada página.

---

## `charts/` — Primitivas de Visualización

Esta capa de abstracción aísla la dependencia de la librería gráfica Recharts. En lugar 
de acoplar la lógica de esta librería en toda la aplicación, el sistema expone siete primitivas 
que se consumen como cajas negras tipadas y a su vez todas operan bajo la directiva `"use client"`.

Las primitivas soportan dos estrategias de color. `BarChart` implementa coloración semántica dinámica 
mediante `colorFn: (valor: number) => string`, que evalúa cada métrica en tiempo de renderizado y asigna 
clases Tailwind sin lógica condicional en los módulos de negocio donde los umbrales se encuentran en `src/lib/analytics.ts`. 
El resto de primitivas (`BarList`, `BubbleChart`, `RingChart`, etc.) usan color estático declarado directamente 
en la serie o el segmento (`color`, `fill`), lo que simplifica los casos donde el valor no determina la codificación visual.

**Matriz de selección de primitivas:**

| Primitiva | Caso de Uso Analítico |
|---|---|
| `BarChart` | Comparativa de una métrica entre categorías |
| `BarList` | Ranking simple sin ejes, más ligero que `BarChart` para top-N listas |
| `BubbleChart` | Correlación entre tres variables simultáneas (x, y, tamaño de burbuja) |
| `RadarChart` | Perfil multi-dimensional de una entidad |
| `RingChart` | Distribución proporcional de una sola dimensión |
| `TemporalAreaChart` | Serie temporal con selector de rango y dos series apiladas |
| `TreemapChart` | Jerarquía donde el área es proporcional a una métrica |

---

### `BarChart`

Componente bidireccional (tanto vertical como horizontal) optimizado para el análisis 
comparativo de métricas a través de dimensiones categóricas. La disposición "vertical" (valor 
por defecto) orienta el eje de ordenadas horizontalmente, garantizando la legibilidad 
tipográfica frente a etiquetas de categoría extensas sin comprometer el área de renderizado.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `data` | `Record<string, any>[]` | requerido | Array de filas con al menos los campos `index` y `category` |
| `index` | `string` | requerido | Clave del campo de etiqueta (eje Y en layout vertical) |
| `category` | `string` | requerido | Clave del campo de valor numérico |
| `valueFormatter` | `(v: number) => string` | `String(v)` | Formatea los valores del eje de cantidades |
| `colorFn` | `(v: number) => string` | — | Color dinámico por valor — tiene prioridad sobre `color` |
| `color` | `string` | `"#6366f1"` | Color fijo para todas las barras |
| `layout` | `"horizontal" \| "vertical"` | `"vertical"` | Orientación del gráfico |
| `yAxisWidth` | `number` | `140` | Ancho del eje de etiquetas (px) |
| `rowHeight` | `number` | `26` | Altura por fila en layout vertical (px) |
| `className` | `string` | `"h-64"` | Clase Tailwind de altura para layout horizontal |

---

### `BarList`

Lista de barras proporcionales sin dependencia de Recharts. Más ligero y apropiado para
rankings donde la jerarquía visual prima sobre la precisión cartesiana.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `data` | `BarItem[]` | requerido | Array `{ name: string; value: number }` |
| `valueFormatter` | `(v: number) => string` | `String(v)` | Formatea el valor a la derecha de cada barra |
| `color` | `string` | `"indigo"` | Color semántico Tailwind: `indigo`, `red`, `violet`, `emerald`, `amber`, `blue` |
| `showRank` | `boolean` | `true` | Muestra el número de posición a la izquierda |

---

### `BubbleChart`

Diagrama de burbujas (scatter + dimensión Z) para correlaciones entre tres variables.
Cada punto tiene coordenadas X e Y más un tamaño de burbuja proporcional a Z. El
tooltip muestra los valores exactos y cualquier metadato adicional que pase `tooltipExtra`.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `series` | `BubbleSeries[]` | requerido | Series `{ name, fill, data: BubblePoint[] }` |
| `xLabel` / `yLabel` | `string` | — | Etiquetas de los ejes |
| `xFormatter` / `yFormatter` | `(v: number) => string` | — | Formatea los ticks de cada eje |
| `zRange` | `[number, number]` | `[60, 380]` | Rango de tamaño de burbuja en píxeles |
| `referenceLines` | `ReferenceLineSpec[]` | `[]` | Líneas de referencia `{ axis, value, color, label? }` |
| `height` | `number` | `340` | Altura del contenedor (px) |
| `tooltipExtra` | `(point: BubblePoint) => ReactNode` | — | Filas adicionales dentro del tooltip |

```typescript
interface BubblePoint  { x: number; y: number; z: number; label: string; meta?: Record<string, string | number> }
interface BubbleSeries { name: string; fill: string; data: BubblePoint[] }
interface ReferenceLineSpec { axis: "x" | "y"; value: number; color: string; label?: string }
```

---

### `RadarChart`

Gráfico de radar multi-serie con panel lateral de valores y toggles interactivos para
activar o desactivar cada serie. Los valores deben estar normalizados en [0–100] porque
todos los ejes tienen la misma escala.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `axes` | `string[]` | requerido | Nombres de los ejes (dimensiones del radar) |
| `series` | `RadarSeries[]` | requerido | Series `{ name, color, values: number[] }` — valores en [0–100] |
| `height` | `number` | `320` | Altura del contenedor (px) |
| `outerRadius` | `string \| number` | `"65%"` | Radio exterior del radar |

---

### `RingChart`

Gráfico de anillo (donut) con etiqueta central, barra de detalle al hacer hover y leyenda
inferior. La etiqueta central muestra un valor resumen y al pasar el cursor sobre un segmento 
la barra de hover muestra el nombre y porcentaje.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `data` | `RingSegment[]` | requerido | Array `{ name, value, color }` |
| `centerLabel` | `string` | requerido | Texto principal en el centro del anillo |
| `centerSub` | `string` | — | Texto secundario bajo `centerLabel` |
| `formatHoverValue` | `(value: number, total: number) => string` | — | Formatea el valor al pasar el cursor |
| `height` | `number` | `180` | Altura del contenedor (px) |
| `centerLabelClass` | `string` | `"text-xl font-black"` | Clases Tailwind del label central |
| `showHoverBar` | `boolean` | `true` | Muestra la barra de detalle al hacer hover |
| `showLegend` | `boolean` | `true` | Muestra la leyenda de colores |

---

### `TemporalAreaChart`

Área apilada con selector de rango temporal (6M / 1A / 2A / Todo) y tooltip fijo a la
izquierda del cursor. El campo `date` de cada fila debe estar en formato `"AAAA-MM"` y es el
frontend quien lo calcula a partir de `year` y `month` antes de pasar los datos al componente.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `data` | `{ date: string }[]` | requerido | Array de filas con campo `date` y los `dataKey` de las series |
| `series` | `AreaSeries[]` | requerido | Series `{ dataKey, label, color, dashed? }` |

---

### `TreemapChart`

Mapa de árbol interactivo donde el área de cada celda es proporcional a su valor. Al hacer
clic en una celda se expande un panel inline con el perfil de esa comunidad o proveedor y
la lista de empresas que la componen. Si hay más de 10 empresas, un botón "Ver todas" abre
un modal portal con la tabla completa.

| Prop | Tipo | Default | Descripción |
|---|---|---|---|
| `data` | `TreemapItem[]` | requerido | Array `{ name, size, fill?, subtitle?, companies?: CompanyInfo[] }` |
| `height` | `number` | `280` | Altura del contenedor (px) |
| `aspectRatio` | `number` | `4/3` | Ratio de aspecto interno del Treemap |
| `showLegend` | `boolean` | `true` | Muestra la leyenda con nombre, conteo y % |
| `colors` | `string[]` | (10 colores) | Paleta de colores en orden cíclico |

---

## `ui/` — Componentes de interfaz genéricos

Este módulo consolida las primitivas estructurales de la interfaz. Sus componentes operan 
completamente desacoplados de la lógica de negocio B2B, actuando como entidades de presentación 
puras. Su objetivo es garantizar la consistencia estética y funcional a través de patrones 
visuales reutilizables, delegando la responsabilidad del contexto y los datos a los 
componentes contenedores que los instancian.

| Componente | Props clave | Descripción |
|---|---|---|
| `StatCard` | `title`, `value`, `unit?`, `delta?`, `trend?` | Tarjeta KPI con valor, unidad y variación porcentual. Acepta `children` para incrustar un `MiniSparkline` |
| `MiniSparkline` | `data: number[]`, `color?` | Línea de tendencia en miniatura renderizada como SVG. Se compone dentro de `StatCard` |
| `HealthStrip` | `economic_volume`, `discrepancy_count`, `global_rate`, `temporal_series` | Franja de tres `StatCard` que resume la salud del grafo en el dashboard |
| `DbStatusBadge` | — | Badge verde/rojo que consume `useDbStatus`. Aparece en la cabecera del `Sidebar` |
| `LoadingState` | `text?` | Spinner centrado. Exporta también `ErrorState` (con mensaje de error) y `EmptyState` |
| `SectionHeader` | `title`, `subtitle?`, `icon?` | Cabecera de sección con icono Heroicon opcional |

---

### Navegación

La estructura de navegación implementa una arquitectura de doble capa. El contenedor 
principal (`SidebarLayout`) centraliza el estado de visibilidad y lo propaga de forma 
descendente (*top-down*) hacia sus subcomponentes mediante propiedades como es el panel 
lateral de escritorio (`Sidebar`) y la cabecera adaptativa para dispositivos móviles (`TopBar`).

### `Sidebar`

Panel de navegación principal estructurado en tres áreas lógicas. El acceso al grupo 
operativo de Sistema (Pipeline) está restringido y su renderizado queda condicionado de 
forma estricta a los privilegios del usuario (`role === "admin"`). 

Para mantener la coherencia con el diseño de estado basado en URL, los enlaces del grupo 
*Analytics* construyen sus rutas inyectando directamente el parámetro de consulta (`?tab=N`). 
Esta decisión arquitectónica delega el control de la vista a la URL, garantizando que todos los 
enlaces actúen como recursos compartibles de forma nativa.

| Grupo | Ítems | Nivel de Acceso |
|---|---|---|
| Main | Visión Global | Todos |
| Analytics | Contratos, Riesgo, Discrepancias, Lead Time, Exposición, Trazabilidad, GDS | Todos |
| Sistema | Pipeline | Solo `role === "admin"` |

### `TopBar`

Barra de navegación adaptativa, visible exclusivamente en resoluciones móviles (`lg:hidden`). 
Actúa como punto de anclaje para la identidad de marca e integra el control interactivo que 
despliega el `Sidebar` superpuesto sobre el contenido (*overlay*).

| Prop | Tipo | Descripción |
|---|---|---|
| `open` | `boolean` | Estado de visibilidad actual del panel lateral |
| `setOpen` | `(v: boolean) => void` | Función mutadora para alternar el estado (*toggle*) |

### `SidebarLayout`

Componente estructural raíz que orquesta la disposición espacial de la aplicación. Implementa 
una lógica de renderizado condicional interceptando la ruta activa mediante el *hook* `usePathname()`. 
Al detectar contextos de acceso público (como `/login`), la infraestructura de navegación 
se desmonta, garantizando una interfaz libre de distracciones para el flujo de autenticación.

---

## `dashboard/` — Componentes de Visualización Macro-Analítica

Este *namespace* agrupa los componentes de interfaz encargados de proyectar la vista 
macroscópica de la red de suministro. Su arquitectura sigue un patrón de 
**componentes contenedores y presentacionales**: la página `app/page.tsx` actúa como el 
único orquestador de red (consumiendo el *endpoint* `GET /api/dashboard/macro`), delegando 
posteriormente la renderización de cada segmento visual hacia los widgets especializados 
mediante inyección de *props*.

| Componente | Responsabilidad Funcional | Dependencia de Datos (`MacroStats`) |
|---|---|---|
| `WelcomeHeader` | Personalización de sesión e identidad | `AuthContext.user.full_name` |
| `KpiGrid` | Panel de mando: totales y salud operativa | `node_counts`, `relationship_counts`, `economic_volume`, `document_health` |
| `TemporalSection` | Auditoría de series temporales | `temporal_series` |
| `RankingsGrid` | Módulo de posiciones competitivas (segmentación) | `doc_type_counts`, `top_suppliers`, `top_buyers` |
| `RankingModal` | Extensión de detalle (modal de visualización completa) | N/A (Consumo interno del estado local) |
| `ScaleFreeSection` | Validación topológica del grafo sintético | `scale_free_metrics` |

*Nota: `RankingModal` se comporta como una extensión controlada por `RankingsGrid` y su activación permite la auditoría de registros completos cuando la densidad de los datos supera el umbral de visualización.*

---

## `pipeline/` — Secciones del formulario

El formulario del pipeline está dividido en tres secciones que agrupan los parámetros
por naturaleza. Las tres comparten el mismo estado `PipelineFormData` que vive en
`PipelinePage` y se pasa hacia abajo de forma que cada sección actualiza su subconjunto 
de campos mediante `setFormData`.

| Sección | Parámetros Controlados | Objetivo Analítico |
|---|---|---|
| `TopologySection` | `rows`, `gamma`, `beta`, `mu`, `min_comm`, `max_comm` | Calibración estructural del modelo LFR. |
| `ConnectivitySection` | `avg_degree_supplies`, `avg_degree_documents`, `avg_degree_products` | Modelado de la densidad relacional en las capas de suministros, documentos y productos. |
| `InfrastructureSection` | `batch_size`, `clear_db`, `use_random_seed`, `seed_value` | Orquestación de persistencia, políticas de limpieza y control de reproducibilidad experimental. |

Todos los controles de entrada implementan una interfaz de doble vía (sliders y campos 
numéricos editables) para asegurar una precisión granular en el ajuste de los hiperparámetros. 
El componente `InfrastructureSection` encapsula el control de ejecución final, sirviendo como 
*gateway* para la puesta en marcha del proceso ETL una vez completada la configuración del modelo.

---

## `analytics/` — Módulos de Visualización Analítica

Este *namespace* agrupa los componentes de dominio encargados de la representación visual de los 
indicadores de negocio. La arquitectura de cada pestaña sigue un patrón de aislamiento de dominio 
por lo que cada componente es autónomo y recibe exclusivamente el *slice* de estado requerido desde 
el árbol global (`AnalyticsState`), garantizando que la mutación o el ciclo de vida de un módulo 
no comprometa la integridad de los adyacentes.

El flujo de datos sigue un modelo de propiedad unidireccional donde el controlador padre (`AnalyticsPage`) 
centraliza la resolución de los artefactos mediante el *hook* `useFetchTab`, el cual persigue una 
estrategia de carga diferida y memoizada. Una vez que los datos residen en el *reducer*, estos se 
inyectan como *props* de solo lectura hacia la pestaña activa, asegurando una capa de presentación 
libre de efectos secundarios.

### Mapa de Cobertura Analítica

| Componente | Tab | Capacidades de Visualización |
|---|---|---|
| `ContractsTab` | 0 | `RingChart` (distribución contractual) y tablas de detalle por proveedor. |
| `RiskTab` | 1 | `TreemapChart` (concentración) y matrices de puntuación, fragilidad y riesgo geográfico. |
| `DiscrepanciesTab` | 2 | `BarChart` (tasa de error) y análisis de impacto comercial (ORDER vs. INVOICE). |
| `LeadTimeTab` | 3 | `BarChart` (análisis de retraso medio por categoría de producto). |
| `ExposureTab` | 4 | Paneles de exposición financiera por proveedor y desglose de deuda vencida. |
| `TraceabilityTab` | 5 | `ChainDiagram` (linaje documental) y tablas de trazabilidad bi-direccional. |
| `GdsTab` | 6 | Diagnóstico de grafos (Centralidad, PageRank, comunidades Louvain y métricas WCC). |

### Componente Especializado: `ChainDiagram`

El componente `ChainDiagram` constituye una excepción en el *namespace* de visualización, ya que no depende 
de las primitivas de Recharts. Su arquitectura consiste en un motor de renderizado SVG que transforma de forma 
dinámica una matriz lineal de nodos (`ChainNode`) en una representación topológica de la cadena de cumplimiento 
(`INVOICE → FULFILLS → DESADV → FULFILLS → ORDER`). Este componente permite al usuario auditar visualmente el 
flujo documental completo, convirtiendo la estructura jerárquica del grafo en una ruta transaccional legible e interpretable.

---

## `auth/` — Módulos de Autenticación y Control de Acceso

Este *namespace* encapsula la interfaz de entrada al sistema, implementando un diseño *responsive* 
con disposición bifurcada para un panel de identidad corporativa y un área funcional de validación. 
Su arquitectura está orientada a facilitar una experiencia de usuario fluida, integrando validaciones 
de formulario en tiempo real y mecanismos de persistencia de sesión seguros.

| Componente | Responsabilidad Funcional |
|---|---|
| `BrandPanel` | Panel izquierdo con logo, descripción del sistema y lista de capacidades |
| `AnimatedNetworkGraph` | Animación SVG de nodos y aristas que se mueven continuamente, ilustrando la topología B2B que el sistema analiza |
| `Capability` | Ítem de la lista de capacidades con iconos Heroicon y texto descriptivo |
| `LoginForm` | Formulario email + contraseña. Al enviar llama a `AuthContext.login()`, que hace el POST y guarda la cookie |
