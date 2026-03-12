# Cómo usar este skill en tu Clawbot (OpenClaw) en Railway

OpenClaw carga los skills desde la carpeta **`skills`** del **workspace**. Para que tu clawbot en Railway use este skill, ese workspace tiene que contener `skills/perfume_product_scraper/`.

El template que usas es **[vignesh07/clawdbot-railway-template](https://github.com/vignesh07/clawdbot-railway-template)**. El workspace por defecto es `OPENCLAW_WORKSPACE_DIR=/data/workspace`; los skills deben estar en `/data/workspace/skills/`.

---

## Si el deploy falló (Build failed / Failed to build an image)

Este repo **solo tiene la carpeta `skills/`**; no trae Dockerfile ni la app de OpenClaw. Si en Railway conectaste este repo como **origen del build** del servicio (por ejemplo con `railway link` + `railway up`), el build fallará.

**Qué hacer:**

1. **Restaurar el build del clawbot** (en Railway Dashboard):
   - Entra al proyecto **overflowing-victory** → servicio **clawdbot-railway-template**.
   - Ve a **Settings** → **Source** (o la pestaña donde se configura el origen del deploy).
   - Vuelve a conectar el repo del template: **https://github.com/vignesh07/clawdbot-railway-template**.  
     (En Railway: “Connect repo” o “Deploy from GitHub” y elige ese repositorio.)
   - Guarda y haz **Redeploy**. El servicio se construirá de nuevo con el Dockerfile del template y el clawbot volverá a arrancar.

2. **No uses este repo (clawbot) como única fuente del servicio.** Este repo solo tiene la carpeta `skills/`; sirve para copiarla dentro del workspace del clawbot, no para reemplazar todo el build.

3. **Añadir el skill** una vez restaurado el build: ver la sección **Template vignesh07/clawdbot-railway-template** más abajo.

Este repo ya está **desvinculado** del servicio (`railway unlink`), así que desde aquí no se volverá a desplegar por accidente.

---

## Template vignesh07/clawdbot-railway-template

Según el [README del template](https://github.com/vignesh07/clawdbot-railway-template), lo que persiste está en el volumen `/data`; el workspace es `/data/workspace`. Los skills deben estar en **`/data/workspace/skills/perfume_product_scraper/`**.

### Opción A: Fork del template e incluir el skill en la imagen

1. Haz **fork** de [vignesh07/clawdbot-railway-template](https://github.com/vignesh07/clawdbot-railway-template) en tu cuenta de GitHub.
2. En el fork, crea la carpeta **`skills/perfume_product_scraper`** en la raíz del repo y copia aquí todo el contenido de `skills/perfume_product_scraper` de este repo (SKILL.md, reference.md, DEPLOY_RAILWAY.md, carpeta `scripts/` con scraper y extractors).
3. Edita el **Dockerfile** del fork y, antes de `COPY src ./src`, añade:
   ```dockerfile
   COPY skills /app/default-skills
   ```
   (así la imagen tendrá `/app/default-skills/perfume_product_scraper/`).
4. El template ejecuta `node src/server.js`. El workspace `/data/workspace` es un volumen que al arrancar puede estar vacío. Hay que copiar los default-skills al volumen la primera vez. Según el README, si existe **`/data/workspace/bootstrap.sh`**, el wrapper lo ejecuta al inicio. En el fork puedes:
   - **Opción 4a:** Documentar que el usuario cree en el volumen (por ejemplo desde `/setup` Debug Console o desde un one-off) un `bootstrap.sh` que haga:
     ```bash
     mkdir -p /data/workspace/skills
     cp -rn /app/default-skills/* /data/workspace/skills/ 2>/dev/null || true
     ```
   - **Opción 4b:** Usar el script **`railway-entrypoint.sh`** que viene en este skill: copia `skills/perfume_product_scraper/railway-entrypoint.sh` a la raíz del fork, en el Dockerfile añade `COPY railway-entrypoint.sh /usr/local/bin/railway-entrypoint.sh`, `RUN chmod +x /usr/local/bin/railway-entrypoint.sh`, luego `ENTRYPOINT ["/usr/local/bin/railway-entrypoint.sh"]` y mantén `CMD ["node", "src/server.js"]`. El script copia `/app/default-skills/*` a `/data/workspace/skills/` solo si cada skill no existe aún, y después ejecuta el comando original. Así el skill se copia automáticamente en el primer arranque.
5. Conecta Railway al **fork** (tu repo de GitHub) en lugar del template original y despliega. Asegura volumen en `/data` y variables `OPENCLAW_WORKSPACE_DIR=/data/workspace`, etc.

### Opción B: Añadir el skill solo en el volumen (sin fork)

Si no quieres hacer fork del template:

1. Cuando el clawbot esté desplegado y funcionando, necesitas escribir en el **volumen** del servicio. Si Railway te da **Shell** o **One-off command** en el contenedor:
   - Crea la ruta `/data/workspace/skills/perfume_product_scraper`.
   - Copia ahí los archivos de este skill (por ejemplo subiéndolos por otro medio o clonando este repo en el contenedor y copiando la carpeta).
2. O usa **Import backup** en `/setup`: si tienes un backup (.tar.gz) que ya incluya `workspace/skills/perfume_product_scraper/`, importarlo rellenará el volumen con ese contenido.
3. Reinicia el servicio (o inicia una nueva sesión en OpenClaw) para que se recarguen los skills.

---

## Opción 1: Este repo ES tu workspace en Railway (recomendado)

Si despliegas OpenClaw en Railway usando **este mismo repositorio** como origen (o como workspace):

1. La carpeta `skills/` ya está en la **raíz del repo** (junto a este archivo está `skills/perfume_product_scraper/`).
2. Configura el servicio en Railway para que el **workspace** de OpenClaw apunte a la raíz del repo. Por ejemplo:
   - Variable: `OPENCLAW_WORKSPACE_DIR` = directorio donde está clonado el repo (p. ej. `/app` o `/data/workspace` si ahí clonas el repo).
   - O si usas el template estándar con volumen en `/data`, clona o copia el repo en `/data/workspace` de forma que exista `/data/workspace/skills/perfume_product_scraper/`.
3. Haz **deploy** (push al repo o “Redeploy” en Railway).
4. Tras el siguiente arranque (o nueva sesión), OpenClaw listará el skill `perfume-product-scraper`.

Resumen: **subir el skill = subir el repo que ya tiene la carpeta `skills/`**. No hace falta “subir” el skill a ningún otro sitio; va incluido en el código.

---

## Opción 2: OpenClaw desplegado con template (one-click) y otro repo

Si tu clawbot en Railway usa el **template oficial** de OpenClaw (one-click) y el workspace es un volumen vacío (p. ej. `/data/workspace`):

1. **Tienes que meter el skill dentro de ese workspace.** Opciones:
   - **A) Desde tu máquina (Railway CLI)**  
     - Instala Railway CLI y enlaza el proyecto.  
     - Ejecuta un comando que copie el contenido de `skills/perfume_product_scraper` al volumen, por ejemplo usando un “one-off” run o un script de init que clone/copie tu repo (o solo la carpeta `skills`) en `/data/workspace`.
   - **B) Repo como fuente del deploy**  
     - Configura el servicio para clonar **este repo** (o un repo que contenga esta carpeta `skills`) en el directorio que usa OpenClaw como workspace, de modo que en el contenedor exista `workspace/skills/perfume_product_scraper/`.
   - **C) Build custom**  
     - En el Dockerfile (o script de build) de tu deploy, copia la carpeta `skills/perfume_product_scraper` a la ruta del workspace (p. ej. `/data/workspace/skills/`) para que esté disponible en cada deploy.

2. Asegúrate de que la ruta final sea exactamente:
   ```text
   <OPENCLAW_WORKSPACE_DIR>/skills/perfume_product_scraper/
   ```
   con `SKILL.md`, `reference.md`, `DEPLOY_RAILWAY.md` y la carpeta `scripts/` dentro.

3. Reinicia el servicio (o inicia una nueva sesión) para que OpenClaw vuelva a escanear los skills.

---

## Dependencias del script (Python)

Si el agente va a **ejecutar** el script `scripts/scraper.py`, el entorno (contenedor o sandbox) debe tener Python y las dependencias:

- En el contenedor: añade en tu Dockerfile o script de inicio algo como:
  ```bash
  pip install -r /data/workspace/skills/perfume_product_scraper/scripts/requirements.txt
  ```
- O documenta en tu equipo que, si se usa un sandbox, el `setupCommand` (o equivalente) instale esas dependencias.

Así el skill no solo estará “subido” (visible), sino que podrá ejecutar el scraper cuando el usuario lo pida.

---

## Comprobar que el skill está cargado

1. Abre la UI de OpenClaw (p. ej. `https://tu-dominio.openclaw.app` o la URL que te dé Railway).
2. Entra en **Settings → Skills** (o el menú donde se listan los skills).
3. Deberías ver **perfume-product-scraper** en la lista.

Si no aparece, revisa que `OPENCLAW_WORKSPACE_DIR` sea correcto y que exista la ruta `.../skills/perfume_product_scraper/SKILL.md`.

---

## Resumen en una frase

**“Subir el skill al clawbot en Railway” = tener la carpeta `skills/perfume_product_scraper` dentro del workspace de OpenClaw en el servidor** (ya sea porque el repo que despliegas incluye `skills/` en la raíz y ese repo es el workspace, o porque copias/clonas ese contenido en el volumen del template).
