# Configuraciones (una por experimento; nunca se editan "en el lugar" para otro experimento)

| Archivo | Punto de la consigna | Contenido |
|---|---|---|
| `config/config_sys1_exp1.json` | Sistema 1 | oscilador amortiguado, 4 integradores, barrido de dt (ECM) |
| `config/config_sys2_exp1a.json` | 2.1.a | N=300 sin obstaculos, energia vs tiempo (plantilla de la campana) |
| `campaigns/campaign_sys2_exp1a.json` | 2.1.a | barrido de dt x 3 seeds (2001-2003) sobre la plantilla anterior; la tanda anterior (seeds 1001-1003) quedó en `output/sys2_exp1a_seeds1001-1003` |
| `config/config_sys2_exp1b.json` y `campaigns/campaign_sys2_exp1b.json` | 2.1.b | obstaculos en contacto (x0=r), tf=30 s, dt=5e-5, N=25..700, 10 seeds (4001-4010), `jobs=1` para medir tiempo; modo `random` para N<400 y `hexagonal` para N>=400 |
| `config/config_sys2_exp1b_energy_check.json` y `campaigns/campaign_sys2_exp1b_energy_check.json` | 2.1.b | verificacion de dt: N=700 hexagonal con obstaculos, dt en {1e-4, 5e-5, 2e-5}, T=10 s |
| `config/config_sys2_exp3.json` y `campaigns/campaign_sys2_exp3.json` | 2.3 | N=100 sin obstaculos, tf=30 s, dt=5e-5, 50 seeds (7001-7050), estados cada 0.02 s |
| `config/config_sys2_exp4.json` y `campaigns/campaign_sys2_exp4.json` | 2.4 | igual que 2.1.b (mismas seeds y modo de condicion inicial) pero tf=600 s y N=25..600; los primeros 30 s coinciden con 2.1.b |
| `config/config_sys2_exp4_long.json` y `campaigns/campaign_sys2_exp4_long.json` | 2.4 | N=500 y 600 con t_max mayor para alcanzar t90/t100: 1200 s (N=500) y 2500 s (N=600); N=700 de 2.1.b se omite; mismas seeds 4001-4010. Reemplaza a los N=500 y 600 de `sys2_exp4` (t_max = 600 s), que quedan censurados |
| `config/config_sys2_exp4b.json` y `campaigns/campaign_sys2_exp4b.json` | 2.4.b | mapa de calor (x0, N): N=50,200,300,400,500 x 9 valores de x0, 10 realizaciones, t_max segun N (100-450 s); las filas N=20 y N=100 se reutilizan de 2.2 y la columna x0=r de N=25-600 de 2.4 |
| `config/config_sys2_exp2.json` | 2.2 | N=100, obstaculos, tmax=100 s (corrida unica de prueba) |
| `config/config_sys2_animation.json` | animacion | N=100, x0=0.25, estados cada 200 pasos |
| `config/config_sys2_animation_N20.json` | animacion | N=20, x0=0.25, estados cada 200 pasos |

Los `contacts.txt` de 2.1.b se reutilizan para 2.4 (t90, t100 vs densidad).

Convencion para los proximos: `config_sys2_exp1b.json` + `campaign_sys2_exp1b.json`, `..._exp2`, `..._exp3`, etc.

Cada corrida guarda en su carpeta de salida `config.json` (copia exacta de lo ejecutado) y cada campana
guarda `campaign.json` y `template.json` en su `outputRoot`. Como `output/` esta en `.gitignore`,
los archivos de `input/` son los que se versionan: commitear la config ANTES de correr.

**Paso temporal fijo del Sistema 2: dt = 5e-5 s** en todos los experimentos (elegido en 2.1.a y verificado con N=700 + obstaculos). Unica excepcion: los barridos de dt de 2.1.a y del chequeo de energia, que lo varian a proposito.
| `campaigns/campaign_sys2_exp4c_x005.json`, `campaigns/campaign_sys2_exp4c_n.json` | 2.4.b | completan la grilla N=50,100,150,200,250,300 x x0=0.05..0.45 (paso 0.05): columna x0=0.05 y filas N=150, 250; 10 realizaciones c/u |
