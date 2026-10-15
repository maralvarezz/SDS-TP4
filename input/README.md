# Configuraciones (una por experimento; nunca se editan "en el lugar" para otro experimento)

| Archivo | Punto de la consigna | Contenido |
|---|---|---|
| `config/config_sys1_exp1.json` | Sistema 1 | oscilador amortiguado, 4 integradores, barrido de dt (ECM) |
| `config/config_sys2_exp1a.json` | 2.1.a | N=300 sin obstaculos, energia vs tiempo (plantilla de la campana) |
| `campaigns/campaign_sys2_exp1a.json` | 2.1.a | barrido de dt x seeds sobre la plantilla anterior |
| `config/config_sys2_exp1b.json` y `campaigns/campaign_sys2_exp1b.json` | 2.1.b | obstaculos en contacto (x0=r), tf=30 s, dt=5e-5, N=25..700, 10 seeds (4001-4010), `jobs=1` para medir tiempo; modo `random` para N<400 y `hexagonal` para N>=400 |
| `config/config_sys2_exp1b_energy_check.json` y `campaigns/campaign_sys2_exp1b_energy_check.json` | 2.1.b | verificacion de dt: N=700 hexagonal con obstaculos, dt en {1e-4, 5e-5, 2e-5}, T=10 s |
| `config/config_sys2_exp3.json` y `campaigns/campaign_sys2_exp3.json` | 2.3 | N=100 sin obstaculos, tf=30 s, dt=5e-5, 10 seeds (7001-7010), estados cada 0.02 s |
| `config/config_sys2_exp2.json` | 2.2 | N=100, obstaculos, tmax=100 s (corrida unica de prueba) |
| `config/config_sys2_animation.json` | animacion | N=100, x0=0.25, estados cada 100 pasos |

Los `contacts.txt` de 2.1.b se reutilizan para 2.4 (t90, t100 vs densidad).

Convencion para los proximos: `config_sys2_exp1b.json` + `campaign_sys2_exp1b.json`, `..._exp2`, `..._exp3`, etc.

Cada corrida guarda en su carpeta de salida `config.json` (copia exacta de lo ejecutado) y cada campana
guarda `campaign.json` y `template.json` en su `outputRoot`. Como `output/` esta en `.gitignore`,
los archivos de `input/` son los que se versionan: commitear la config ANTES de correr.
