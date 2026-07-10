# Evaluación Final Transversal — Tecnologías de Virtualización

**Estudiante:** Germán Muñoz Manríquez  
**Asignatura:** DIY7111 — Tecnologías de Virtualización  
**Proyecto:** VZeta — Aplicación web contenerizada en AWS EC2

---

## 1. Descripción general

Este proyecto implementa una aplicación web contenerizada sobre una instancia EC2 de AWS Learner Lab. La solución utiliza Docker Engine y Docker Compose para ejecutar tres servicios:

1. **mynginx_container:** NGINX como reverse proxy y punto de entrada por HTTP/80.
2. **myapp_container:** aplicación propia desarrollada en Python y Flask.
3. **db_container:** PostgreSQL con volumen persistente.

Cada acceso a la ruta `/` registra una visita en PostgreSQL y muestra el contador acumulado. Los datos permanecen almacenados aunque los contenedores sean detenidos y creados nuevamente.

---

## 2. Arquitectura

```text
Cliente web
    |
    | HTTP/80
    v
+------------------------- AWS EC2 --------------------------+
|                                                             |
|  +-------------------+      +---------------------------+   |
|  | mynginx_container | ---> | myapp_container           |   |
|  | NGINX :80         |      | Flask/Gunicorn :5000      |   |
|  +-------------------+      +-------------+-------------+   |
|                                           |                 |
|                                           v                 |
|                              +---------------------------+  |
|                              | db_container              |  |
|                              | PostgreSQL :5432          |  |
|                              +-------------+-------------+  |
|                                            |                |
|                                 volumen persistente         |
|                                 vzeta_postgres_data         |
+-------------------------------------------------------------+
```

Los tres servicios utilizan la red bridge `vzeta_network`. Solo NGINX publica un puerto hacia el host. Flask y PostgreSQL permanecen accesibles únicamente desde la red interna de Docker.

---

## 3. Justificación técnica: contenedores frente a hipervisores

### 3.1 Virtualización tradicional

Un hipervisor permite ejecutar varias máquinas virtuales, cada una con su propio sistema operativo invitado. Esta tecnología proporciona un alto nivel de aislamiento y es adecuada cuando se requieren sistemas operativos diferentes, compatibilidad con aplicaciones heredadas o separación completa entre cargas.

Sin embargo, cada máquina virtual necesita memoria, CPU, almacenamiento y mantenimiento para su sistema operativo. También puede requerir licencias adicionales según el hipervisor y los sistemas operativos empleados. Su despliegue y arranque normalmente es más lento que el de un contenedor.

### 3.2 Contenedores Docker

Los contenedores comparten el kernel del sistema operativo anfitrión y empaquetan la aplicación junto con sus dependencias. Esto reduce el consumo de recursos, acelera el inicio y facilita la portabilidad entre ambientes compatibles con Docker.

Para el caso VZeta, Docker es adecuado porque:

- La aplicación está formada por componentes independientes.
- No se requiere virtualizar sistemas operativos completos.
- Docker Compose permite administrar el stack desde un único archivo.
- El entorno no permite Kubernetes ni servicios gestionados como EKS.
- La aplicación debe desplegarse rápidamente en una única instancia EC2.
- Las imágenes permiten reproducir el entorno de manera consistente.
- El volumen de PostgreSQL resuelve la persistencia de datos.

### 3.3 Comparación resumida

| Criterio | Hipervisores y VM | Contenedores Docker |
|---|---|---|
| Unidad desplegada | Sistema operativo completo | Aplicación y dependencias |
| Consumo de recursos | Mayor | Menor |
| Tiempo de arranque | Habitualmente mayor | Habitualmente menor |
| Aislamiento | Fuerte, mediante VM | A nivel de procesos y namespaces |
| Portabilidad | Imágenes de VM de mayor tamaño | Imágenes livianas y reproducibles |
| Administración | SO, parches y aplicación | Imagen, contenedor y aplicación |
| Uso recomendado | SO distintos, aplicaciones heredadas | Aplicaciones web y microservicios |
| Orquestación del caso | No necesaria | Docker Compose a nivel de host |

### 3.4 Instalación y licenciamiento

En una plataforma tradicional on-premise se debe validar la compatibilidad del hardware, habilitar virtualización en BIOS/UEFI, instalar el hipervisor, configurar redes y datastores y revisar el licenciamiento del proveedor. Además, los sistemas operativos invitados pueden requerir licencias propias.

Docker Engine permite ejecutar contenedores sobre Linux con una instalación más liviana. En este proyecto se utiliza una instancia EC2 con Linux y componentes de código abierto. En un entorno empresarial real se deben revisar las condiciones vigentes del proveedor, el soporte requerido y las políticas internas antes de elegir una edición o producto.

---

## 4. Propuesta para nube pública, privada e híbrida

### Nube pública

La nube pública es apropiada para cargas que necesitan aprovisionamiento rápido, elasticidad y pago según consumo. Para VZeta, AWS EC2 permite desplegar Docker sin adquirir infraestructura física. Su principal desventaja es la dependencia del proveedor y la necesidad de controlar costos, identidades y exposición de red.

### Nube privada

Una nube privada permite mantener mayor control sobre datos, redes y cumplimiento. Puede implementarse sobre VMware, Hyper-V, Proxmox u otra plataforma interna. Requiere inversión, capacidad operativa, respaldo, monitoreo y renovación de hardware.

### Nube híbrida

Una arquitectura híbrida combina servicios públicos y privados. Por ejemplo, la capa web puede ejecutarse en nube pública y consumir servicios internos mediante VPN o conectividad privada. Esta alternativa aporta flexibilidad, pero aumenta la complejidad de red, identidad, observabilidad y gobierno.

### Recomendación

Para esta evaluación y para una aplicación pequeña, la alternativa recomendada es AWS EC2 con Docker Compose. Para un entorno productivo de mayor escala sería razonable evolucionar hacia un orquestador o servicio gestionado, siempre que los requisitos de disponibilidad, operación y presupuesto lo justifiquen.

---

## 5. Estructura del repositorio

```text
.
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   ├── default.conf
│   └── Dockerfile
├── evidencias/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## 6. Creación de la instancia EC2

Configuración solicitada:

- Región: `us-east-1`
- Key pair: `vockey`
- Tipo: `small`, según disponibilidad del laboratorio
- Sistema operativo: Ubuntu Server
- Security Group:
  - TCP/22 desde la IP administrativa
  - TCP/80 desde Internet para la demostración

> En un entorno productivo, SSH no debe exponerse a todo Internet. Se recomienda restringirlo a una IP administrativa, utilizar un bastion host o un servicio de administración remota.

### Evidencia 1 — Instancia EC2

![Instancia EC2 creada](evidencias/01-ec2.png)

---

## 7. Instalación de Docker y Docker Compose

Conectarse a la instancia:

```bash
ssh -i labsuser.pem ubuntu@IP_PUBLICA_EC2
```

Actualizar paquetes:

```bash
sudo apt update
sudo apt upgrade -y
```

Instalar Docker Engine y el plugin Compose desde los repositorios disponibles en la instancia:

```bash
sudo apt install -y docker.io docker-compose-v2 git
```

Habilitar e iniciar Docker:

```bash
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager
```

Agregar el usuario al grupo Docker:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Validar:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

### Evidencia 2 — Docker instalado

![Docker instalado](evidencias/02-docker-version.png)

---

## 8. Descarga y preparación del proyecto

```bash
git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO
```

Crear el archivo de variables:

```bash
cp .env.example .env
nano .env
```

Ejemplo:

```dotenv
DB_NAME=vzeta_db
DB_USER=vzeta_user
DB_PASSWORD=CLAVE_SEGURA
```

El archivo `.env` está excluido mediante `.gitignore` para evitar publicar credenciales.

---

## 9. Construcción de imágenes

Construcción explícita de la imagen Flask:

```bash
docker build -t vzeta/myapp:1.0 ./app
```

Construcción explícita de la imagen NGINX:

```bash
docker build -t vzeta/mynginx:1.0 ./nginx
```

También pueden construirse todas las imágenes declaradas en Compose:

```bash
docker compose build
```

Verificación:

```bash
docker images
```

### Evidencia 3 — Imágenes construidas

![Imágenes Docker](evidencias/03-docker-images.png)

---

## 10. Despliegue con Docker Compose

Validar la configuración:

```bash
docker compose config
```

Levantar el stack:

```bash
docker compose up -d
```

Comprobar los servicios:

```bash
docker compose ps
docker ps
```

### Evidencia 4 — Stack levantado

![Docker Compose operativo](evidencias/04-compose-ps.png)

---

## 11. Pruebas de funcionamiento

Desde la instancia:

```bash
curl http://localhost/
```

Desde un equipo externo:

```bash
curl http://IP_PUBLICA_EC2/
```

También se puede abrir en el navegador:

```text
http://IP_PUBLICA_EC2/
```

Actualizar varias veces la página para comprobar que el contador aumenta.

### Evidencia 5 — Aplicación funcionando

![Aplicación en navegador](evidencias/05-aplicacion.png)

### Evidencia 6 — Prueba con curl

![Prueba curl](evidencias/06-curl.png)

---

## 12. Comprobación de persistencia

Consultar los volúmenes:

```bash
docker volume ls
```

Revisar el volumen desde Compose:

```bash
docker volume inspect vzeta_postgres_data
```

Observar el contador actual en el navegador y luego detener y eliminar los contenedores sin eliminar el volumen:

```bash
docker compose down
docker compose up -d
```

Esperar hasta que los servicios estén saludables:

```bash
docker compose ps
```

Volver a ingresar a la aplicación. El contador debe continuar desde el valor almacenado.

> No utilizar `docker compose down -v` durante la prueba, porque la opción `-v` elimina los volúmenes declarados.

### Evidencia 7 — Volumen creado

![Volumen persistente](evidencias/07-volume-ls.png)

### Evidencia 8 — Persistencia comprobada

![Persistencia del contador](evidencias/08-persistencia.png)

---

## 13. Uso de Docker Inspect

### 13.1 Mounts del contenedor PostgreSQL

```bash
docker inspect db_container
```

Mostrar únicamente la sección `Mounts`:

```bash
docker inspect db_container \
  --format '{{json .Mounts}}'
```

Versión legible con Python:

```bash
docker inspect db_container \
  --format '{{json .Mounts}}' | python3 -m json.tool
```

### 13.2 Inspección de la red

```bash
docker network inspect vzeta_network
```

### 13.3 Inspección de la imagen

```bash
docker image inspect vzeta/myapp:1.0
```

### Evidencia 9 — Mounts de PostgreSQL

![Inspect Mounts](evidencias/09-inspect-mounts.png)

### Evidencia 10 — Red Docker

![Inspect red](evidencias/10-inspect-network.png)

### Evidencia 11 — Imagen Flask

![Inspect imagen](evidencias/11-inspect-image.png)

---

## 14. Ciclo de vida de contenedores e imágenes

Estas operaciones deben realizarse después de documentar el funcionamiento y la persistencia.

### Logs

```bash
docker logs myapp_container
docker logs mynginx_container
docker logs db_container
```

Seguimiento en tiempo real:

```bash
docker logs -f myapp_container
```

### Estadísticas

```bash
docker stats
```

Para salir, presionar `Ctrl+C`.

### Reinicio

```bash
docker restart myapp_container
docker ps
```

### Detención

```bash
docker stop mynginx_container
docker ps -a
```

Restauración:

```bash
docker start mynginx_container
```

### Renombrado

Docker Compose espera el nombre definido en `container_name`. Por ello, el renombrado se demuestra y luego se revierte:

```bash
docker stop myapp_container
docker rename myapp_container myapp_container_demo
docker ps -a
docker rename myapp_container_demo myapp_container
docker start myapp_container
```

### Eliminación de contenedor

Para evitar afectar la base de datos, se puede eliminar y recrear NGINX:

```bash
docker stop mynginx_container
docker rm mynginx_container
docker compose up -d mynginx
```

### Eliminación de imagen

Primero eliminar el contenedor que usa la imagen y luego eliminarla:

```bash
docker compose stop mynginx
docker compose rm -f mynginx
docker rmi vzeta/mynginx:1.0
docker compose up -d --build mynginx
```

### Estado final

Al terminar las demostraciones, dejar el stack completamente operativo:

```bash
docker compose up -d --build
docker compose ps
curl http://localhost/
```

### Evidencia 12 — Logs

![Docker logs](evidencias/12-logs.png)

### Evidencia 13 — Estadísticas

![Docker stats](evidencias/13-stats.png)

### Evidencia 14 — Operaciones de ciclo de vida

![Ciclo de vida](evidencias/14-ciclo-vida.png)

---

## 15. Comandos de diagnóstico

Estado general:

```bash
docker compose ps
```

Logs del stack:

```bash
docker compose logs --tail=100
```

Comprobar NGINX:

```bash
curl -I http://localhost/
```

Comprobar la aplicación desde la red Docker:

```bash
docker exec mynginx_container wget -q -O - http://myapp:5000/health
```

Comprobar PostgreSQL:

```bash
docker exec db_container \
  pg_isready -U "$DB_USER" -d "$DB_NAME"
```

Revisar tabla y cantidad de visitas:

```bash
docker exec -it db_container \
  psql -U vzeta_user -d vzeta_db \
  -c "SELECT COUNT(*) AS total_visitas FROM visits;"
```

---

## 16. Buenas prácticas aplicadas

- Solo NGINX publica un puerto hacia el host.
- PostgreSQL y Flask permanecen en una red interna.
- Se utiliza un volumen nombrado para persistencia.
- Las credenciales se reciben mediante variables de entorno.
- `.env` no se publica en GitHub.
- Los servicios incluyen healthchecks.
- La aplicación utiliza reintentos de conexión a PostgreSQL.
- La imagen Flask ejecuta el proceso con un usuario sin privilegios.
- Las imágenes se basan en variantes `slim` y `alpine`.
- La aplicación se ejecuta mediante Gunicorn en lugar del servidor de desarrollo de Flask.
- Los contenedores se reinician automáticamente salvo detención manual.

---

## 17. Errores comunes

### El puerto 80 no responde

Revisar:

```bash
sudo ss -lntp | grep ':80'
docker compose ps
docker compose logs mynginx
```

También se debe comprobar que el Security Group permita TCP/80.

### La aplicación no conecta a PostgreSQL

Revisar:

```bash
docker compose logs db
docker compose logs myapp
docker network inspect vzeta_network
```

El host de base de datos debe ser `db`, que corresponde al nombre del servicio Compose, no `localhost`.

### El contador vuelve a cero

Comprobar que el volumen exista:

```bash
docker volume inspect vzeta_postgres_data
```

No utilizar:

```bash
docker compose down -v
```

porque elimina el volumen.

### Permiso denegado al ejecutar Docker

Aplicar:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

---

## 18. Limpieza de recursos

Para detener el stack sin borrar datos:

```bash
docker compose down
```

Para borrar contenedores, red y volumen:

```bash
docker compose down -v
```

> Esta última operación elimina los datos de PostgreSQL y solo debe realizarse cuando ya no se necesiten las evidencias.

Al finalizar el laboratorio, detener o eliminar la instancia EC2 para evitar el consumo innecesario del presupuesto.
