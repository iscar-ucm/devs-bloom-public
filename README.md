<a name="readme-top"></a>

<br />
<div align="center">
    <img src="doc/DEVS_BLOOM-DB-SensoresInternos.svg" alt="Logo" width="800" height="500">
  </a>
<h3 align="center">Devs-Bloom</h3>
  <p align="center">
    Repositorio para la especificación del modelo completo del proyecto IA-GES-BLOOM-CM
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Tabla de contenidos</summary>
  <ol>
    <li>
      <a href="#about-the-project">Sobre el proyecto</a>
    </li>
    <li>
      <a href="#getting-started">Pasos iniciales</a>
      <ul>
        <li><a href="#prerequisites">Requisitos</a></li>
        <li><a href="#installation">Instalación</a></li>
        <li><a href="#recomendations">Recomendaciones</a></li>
      </ul>
    </li>
    <li><a href="#license">Licencia</a></li>
    <li><a href="#license">Contactos</a></li>
    <li><a href="#acknowledgments">Agradecimientos</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## Sobre el proyecto
Las floraciones de cianobacterias (CBs), que ocurren tanto en aguas continentales como marítimas, plantean
amenazas a los ambientes naturales al producir toxinas que afectan por igual a la salud de humanos y animales. En el pasado, las CBs se evaluaban principalmente mediante la recopilación manual
y posterior análisis de muestras de agua, y ocasionalmente de manera automática por
instrumentos que adquieren información de algunas ubicaciones fijas. Estos procedimientos
no proporcionan datos con la resolución espacial y temporal deseable para
anticipar la formación de CBs. Por lo tanto, se necesitan nuevas herramientas y tecnología para
detectar, caracterizar y responder eficientemente a los CBs que amenazan la calidad del
agua. Esto es especialmente importante hoy en día, cuando el suministro de agua del mundo está
bajo una gran presión por el cambio climático, la sobreexplotación y la contaminación. Este
proyecto presenta DEVS-BLOOM, un marco novedoso para el monitoreo en tiempo real
y gestión de CBs. Su propósito es apoyar riesgos de alto rendimiento.
detección con Ingeniería de Sistemas Basada en Modelos (MBSE) e Infraestructura de Internet de
las cosas (IoT) para entornos dinámicos.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Pasos Iniciales

A continuación, se indicarán los pasos a seguir para la instalación del software necesario para el correcto funcionamiento del simulador.

### Requisitos mínimos
Los programas empleados a lo largo de toda la instalación de los paquetes de software se muestran a continuación:

* [Visual Studio Code](https://code.visualstudio.com/Download)
* [Python](https://www.python.org/downloads/)  (Versión recomendada 3.10)
* [Git](https://git-scm.com/downloads) (Necesario para trabajar en colaboración con el repositorio del proyecto)
* [Extensiones](https://marketplace.visualstudio.com/VSCode) para Visual Studio 
    ```sh
    Python + Pylance / Jupyter + Jupyter Cell Tag + Jupyter Keymap + Jupyter Slide Show + Jupyther Notebook Renderers
    ```
### Instalación

1. Crear una carpeta local en la ubicación donde se desee alojar el proyecto una vez se tengan instalados los programas necesarios.
2. Clonar el repositorio dentro la carpeta seleccionada.
   ```sh
   git clone https://github.com/iscar-ucm/devs-bloom.git
   ```
3. Incluir el fichero `Washington-1m-2008-09_UGRID.nc` en la carpeta [dataedge/](https://github.com/iscar-ucm/devs-bloom/tree/main/dataedge). Descarga dispolible en el siguiente [enlace](https://drive.google.com/file/d/19ebVEwIzA0eD7wIkQ5ijRXtAgXljbC0h/view?usp=share_link) de Google Drive.

4. Instalar los paquetes de software que serán empleados (se recomienda usar la herramienta pip)
   ```sh
   pip install xdevs
   pip install pandas
   pip install matplotlib
   pip install scipy 
   pip install netCDF4 
   pip install bokeh   
   pip install pyproj 
   pip install requests
   pip install flask  
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Recomendaciones
* Extensiones útiles para la visualización de algunos ficheros en VSC:  
    ```sh
    Rainbow CSV, Excel Viewer, Docker, Draw.io Integration...
    ```
* Se recomienda trabajar sobre la carpeta que se haya seleccionado con todos los ficheros en local.


<!-- USAGE EXAMPLES -->
## Uso
_Para más ejemplos, dirigirse a la [Documentación](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

- [x] Versión 1.0 
    - [ ] Rama 1
    - [ ] Rama 2
- [x] Versión 2.0.0 - Lazo con Inferencia
    - [x] Rama devel
      - [ ] Clase Servicios en carpeta externa  
      - [ ] Incorporación de actuador externo

Para ver más información, acceder a [Ramas](https://github.com/iscar-ucm/devs-bloom/branches)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## Licencia


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contacto

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Agradecimientos

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
