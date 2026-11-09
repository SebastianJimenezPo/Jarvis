# Diagnóstico de problemas

**DEGRADED al primer inicio:** todavía no existe la referencia. Cierra Jarvis y calibra; o comprueba que se compiló el auxiliar. El error exacto está en el menú de diagnósticos y en `%LOCALAPPDATA%\JarvisCore\logs`.

**No aparece el icono:** revisa los iconos ocultos de la bandeja de Windows. Prueba `python -m jarvis --debug`. Si la bandeja no existe en la sesión, se informa del error en vez de dejar una captura invisible.

**Micrófono denegado o sin datos:** revisa permisos de micrófono para aplicaciones de escritorio y el dispositivo de entrada de Windows. Cierra aplicaciones que lo usen en exclusivo. Los reintentos son limitados; usa «Reanudar / reintentar» después de corregirlo.

**Micrófono fijo ausente:** conecta el dispositivo o selecciona `auto`. El modo fijo no hace fallback silencioso. Si dos dispositivos comparten nombre, la selección se rechaza; cambia su nombre en Windows. Cambiar salida de audio también puede producir un breve reinicio conservador del flujo cuando Windows anuncia cambios de endpoints.

**Auriculares Bluetooth:** abrir el micrófono puede activar el perfil manos libres de Windows y cambiar la calidad del audio reproducido. Para jugar o escuchar música puede convenir fijar el micrófono Realtek/USB; esto requiere decidirlo según el dispositivo, no una promesa de compatibilidad universal.

**Configuración dañada:** `--reset-config` conserva una copia y restaura valores predeterminados. Las referencias no se borran.

**Otra instancia activa:** el segundo proceso no abre micrófono. Cierra la instancia de la bandeja antes de calibrar. El mutex se libera al salir; no se usan archivos PID residuales.

**No funciona el inicio automático:** `install_startup.ps1 -ValidateOnly` verifica los objetos y las rutas. Examina el Programador de tareas y su historial. Si cambias la carpeta, vuelve a instalar la tarea. Se ejecuta al iniciar sesión, no antes de que exista escritorio. No cambies a servicio de sesión 0.

**El sonido de confirmación no se oye:** depende del esquema de sonidos de Windows. Verifica primero el estado `AWAKE` y el evento en registros. Desactiva `confirmation` si prefieres silencio.

**Cierre lento:** el watchdog del detector puede tardar dos segundos; el arranque de un auxiliar tiene un plazo de 15 s. La GUI no bloquea su bucle al abrir recursos. El cierre espera al controlador y registra si no termina; un controlador nativo de audio atascado fuera del control de Python sigue siendo un riesgo que necesita pruebas físicas prolongadas.
