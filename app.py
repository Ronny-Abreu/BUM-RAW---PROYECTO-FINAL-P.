from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

#creamos el servidor flask
app = Flask(__name__)
#Clave secreta para evitar que el usuario pueda modoficar los datos de la sesion
app.secret_key = 'GodIsGod07'

# Configuración de la base de datos
try:
    db = mysql.connector.connect(
        host="mysql.railway.internal", 
        port=3306,  
        user="root",  
        password="FFEaUztTHCYcumImFaKsphYSzTefgstp",  
        database="railway"
    )
    cursor = db.cursor()
    print("Conexión a la base de datos exitosa!")
except mysql.connector.Error as err:
    print(f"Error al conectar a la base de datos: {err}")
    exit()  # Salir si hay un error de conexión


#DATOS DEL USUARIO ADMINISTRADOR:

#correo_admin = 'admin@gmail.com'
#contrasena_admin = 'admin1234'


# Ruta para la página principal
@app.route("/")
def pagina_principal():
    usuario = session.get('usuario')  # Obtiene el usuario de la sesión
    
    #Si la cuenta existe, inica sesion y lo redirige a la pagina principal y el nombre del usuario con el que inició sesion
    return render_template("PanelPrincipal.html", usuario=usuario)

@app.route("/chatbot")
def chatbot():
    if 'usuario' in session:
        return redirect("https://t.me/BumRawBot")
    else:
        return redirect(url_for("inicio_sesion"))


# Ruta para la página de inicio de sesión  
@app.route("/inicioSesion", methods=["GET", "POST"])
def inicio_sesion():
    if request.method == "POST":
        # strip() Limpia espacios en blanco que se dejan a los alrededores
        correo = request.form["correo"].strip()
        contrasena = request.form["contrasena"].strip()
        
        # Consultar usuario
        query = "SELECT nombre, contrasena, es_admin FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash("El usuario no existe. Por favor, regístrese primero.", "danger")
            return render_template("IniciarSesion.html")
        
        # Comparar contraseña ingresada con el hash almacenado
        if check_password_hash(usuario[1], contrasena):
            # Almacena la sesión del usuario
            session['usuario'] = usuario[0]
            session['es_admin'] = usuario[2]  # Guardar el valor es_admin
            return """
                <html>
                <body>
                    <script>
                        console.log('Inicio de sesión exitoso. Recargando la página principal.');
                        if (window.opener) {
                            window.opener.location.reload();  // Recarga la página principal
                            window.close();  // Cierra la ventana
                        } else {
                            console.error('No se pudo cerrar la pestaña. Asegúrate de que esta ventana fue abierta por otra.');
                            if (confirm('Inicio de sesión exitoso. ¿Cerrar esta pestaña?')) {
                                window.close();  // Cierra la pestaña cuando el usuario hace clic en "Aceptar"
                            }
                        }
                    </script>
                </body>
                </html>
            """
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
    
    return render_template("IniciarSesion.html")


@app.route("/reporte", methods=["GET", "POST"])
def reporte():
    if not session.get('es_admin'):
        flash("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for('pagina_principal'))

    # Obtener el valor del input (campo de búsqueda 'correo')
    correo_busqueda = request.args.get('correo')  # Captura lo que se escribe en el campo de búsqueda
    
    # Si el input está vacío, mostrar todos los usuarios
    if correo_busqueda:
        # Si hay un valor en el campo de búsqueda, buscar coincidencias parciales en los correos
        query = "SELECT nombre, correo FROM usuarios WHERE correo LIKE %s"
        cursor.execute(query, ('%' + correo_busqueda + '%',))  # Buscar todos los usuarios cuyo correo contenga el texto ingresado
    else:
        # Si no hay valor en el campo de búsqueda (input vacío), mostrar todos los usuarios
        query = "SELECT nombre, correo FROM usuarios"
        cursor.execute(query)
    
    usuarios = cursor.fetchall()  # Obtiene todos los resultados según la búsqueda

    # Asegurarse de que la base de datos se haya actualizado correctamente
    db.commit()

    # Crear la respuesta para evitar caché del navegador
    response = make_response(render_template("reporte.html", usuarios=usuarios))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response





# Ruta para la página de recuperación de contraseña
@app.route("/recuperarContrasena", methods=["GET", "POST"])
def recuperar_contrasena():
    if request.method == "POST":
        correo = request.form["correo"].strip()
        nueva_contrasena = request.form["contrasena"].strip()

        # Verificar si el correo existe en la base de datos
        query = "SELECT * FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        usuario = cursor.fetchone()

        if usuario:
            # Si el correo existe, actualizar la contraseña
            hash_contrasena = generate_password_hash(nueva_contrasena)
            query_update = "UPDATE usuarios SET contrasena = %s WHERE correo = %s"
            cursor.execute(query_update, (hash_contrasena, correo))
            db.commit()
            flash("Contraseña actualizada exitosamente.", "success")
            return redirect(url_for("inicio_sesion"))
        else:
            flash("El correo no está registrado. Por favor, ingrese un correo válido.", "danger")
    
    return render_template("recuperarContrasena.html")


@app.route("/cerrarSesion")
def cerrar_sesion():
    session.pop('usuario', None)  # Eliminar usuario de la sesión
    session.pop('es_admin', None)  # Eliminar es_admin de la sesión
    flash("Has cerrado sesión exitosamente.", "success")
    return redirect(url_for("pagina_principal"))



# Ruta para la página de registro
@app.route("/registrarse", methods=["GET", "POST"])
def registrarse():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip()
        contrasena = generate_password_hash(request.form["contrasena"].strip())
        
        # Comprobar si el correo ya existe en la base de datos
        query = "SELECT * FROM usuarios WHERE correo = %s"
        cursor.execute(query, (correo,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            flash("La cuenta ya existe con este correo.", "danger")
            return render_template("registrarse.html")  # Mantener al usuario en la misma página
        
        try:
            query = "INSERT INTO usuarios (nombre, correo, contrasena) VALUES (%s, %s, %s)"
            cursor.execute(query, (nombre, correo, contrasena))
            db.commit()
            flash("Usuario registrado con éxito, inicia sesión.", "success")
            return redirect(url_for("registrarse"))
        except Exception as e:
            flash(f"Ocurrió un error: {str(e)}", "danger")
            return render_template("registrarse.html")
    
    return render_template("registrarse.html")


@app.route("/planesInicio")
def planes_inicio():
    if 'usuario' in session:
        return render_template("planesInicio.html")
    else:
        return redirect(url_for("inicio_sesion"))


# Página de destino después de iniciar sesión
@app.route("/paginainformativa")
def paginainformativa():
    return render_template("paginainformativa.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
