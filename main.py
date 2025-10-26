from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "clave_secreta_para_la_app"

# ----- CONFIGURACIÓN -----
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# Horarios disponibles por día
HORARIOS = [
    "10:00 - 12:00",
    "12:00 - 14:00",
    "17:00 - 18:30",
    "18:30 - 20:00"
]

# Base de datos simulada (en memoria)
usuarios = {"admin": {"password": "1234", "is_admin": True}}
reservas = {}
bloqueos = []

# ----- FUNCIONES -----
def fecha_actual():
    return datetime.now().date()

def fechas_disponibles():
    hoy = fecha_actual()
    return [hoy + timedelta(days=i) for i in range(0, 15)]  # 14 días vista

# ----- RUTAS -----
@app.route("/")
def inicio():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("reservar"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]
        if usuario in usuarios and usuarios[usuario]["password"] == clave:
            session["usuario"] = usuario
            return redirect(url_for("reservar"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

@app.route("/reservar", methods=["GET", "POST"])
def reservar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    user = session["usuario"]

    if request.method == "POST":
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        if (fecha, hora) in bloqueos:
            mensaje = "Este horario está bloqueado por el administrador."
        elif any(r["usuario"] == user for r in reservas.values()):
            mensaje = "Ya tienes una reserva activa."
        else:
            reservas[(fecha, hora)] = {"usuario": user}
            mensaje = "Reserva realizada correctamente."
        return render_template("reservas.html", usuario=user, fechas=fechas_disponibles(),
                               horarios=HORARIOS, reservas=reservas, bloqueos=bloqueos, mensaje=mensaje)

    return render_template("reservas.html", usuario=user, fechas=fechas_disponibles(),
                           horarios=HORARIOS, reservas=reservas, bloqueos=bloqueos)

@app.route("/cancelar/<fecha>/<hora>")
def cancelar(fecha, hora):
    if "usuario" not in session:
        return redirect(url_for("login"))
    user = session["usuario"]

    clave = (fecha, hora)
    if clave in reservas and reservas[clave]["usuario"] == user:
        hora_inicio = datetime.strptime(hora.split(" - ")[0], "%H:%M").time()
        fecha_hora_reserva = datetime.combine(datetime.strptime(fecha, "%Y-%m-%d").date(), hora_inicio)
        if datetime.now() < fecha_hora_reserva - timedelta(hours=1):
            reservas.pop(clave)
        else:
            return "No se puede cancelar con menos de 1 hora de antelación."
    return redirect(url_for("reservar"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "usuario" not in session or session["usuario"] != "admin":
        return redirect(url_for("login"))

    mensaje = ""
    if request.method == "POST":
        if "nuevo_usuario" in request.form:
            nuevo = request.form["nuevo_usuario"]
            clave = request.form["clave_usuario"]
            usuarios[nuevo] = {"password": clave, "is_admin": False}
            mensaje = f"Usuario '{nuevo}' creado correctamente."
        elif "bloquear_fecha" in request.form:
            fecha = request.form["bloquear_fecha"]
            hora = request.form["bloquear_hora"]
            bloqueos.append((fecha, hora))
            mensaje = "Horario bloqueado correctamente."

    return render_template("admin.html", usuarios=usuarios, fechas=fechas_disponibles(),
                           horarios=HORARIOS, bloqueos=bloqueos, mensaje=mensaje)

# ----- EJECUCIÓN LOCAL -----
if __name__ == "__main__":
    app.run(debug=True)
