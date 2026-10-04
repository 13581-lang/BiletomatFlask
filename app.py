
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
import time

app = Flask(__name__)
app.secret_key = "biletomat-secret-key"

# zaladuj ceny
with open("prices.json", "r", encoding="utf-8") as jf:
    prices = json.load(jf)

def get_cart():
    return session.get("cart", [])

def get_cart_value(cart):
    return round(sum(t["price"] for t in cart), 2)

def save_cart(cart):
    session["cart"] = cart

@app.route("/")
def index():
    cart = get_cart()
    total = get_cart_value(cart)
    return render_template("index.html", prices=prices, cart=cart, total=total)

@app.route("/add", methods=["POST"])
def add_ticket():
    discount = request.form.get("discount")
    ticket_type = request.form.get("type")
    validity = request.form.get("validity")

    if not discount or not ticket_type or not validity:
        flash("Wybierz wszystkie opcje biletu!", "error")
        return redirect(url_for("index"))

    try:
        price = prices[discount][ticket_type][validity]
    except KeyError:
        flash("Nieprawidłowa kombinacja biletu!", "error")
        return redirect(url_for("index"))

    ticket = {
        "discount": discount,
        "type": ticket_type,
        "validity": validity,
        "price": price
    }

    cart = get_cart()
    cart.append(ticket)
    save_cart(cart)
    flash(f"Dodano: {discount} {ticket_type} {validity} - {price} zł", "success")
    return redirect(url_for("index"))

@app.route("/remove/<int:index>")
def remove_ticket(index):
    cart = get_cart()
    if 0 <= index < len(cart):
        removed = cart.pop(index)
        save_cart(cart)
        flash(f"Usunięto bilet: {removed['discount']} {removed['type']} {removed['validity']}", "info")
    return redirect(url_for("index"))

@app.route("/clear")
def clear_cart():
    save_cart([])
    flash("Koszyk wyczyszczony", "info")
    return redirect(url_for("index"))

@app.route("/pay", methods=["POST"])
def pay():
    cart = get_cart()
    if not cart:
        flash("Koszyk jest pusty!", "error")
        return redirect(url_for("index"))

    method = request.form.get("payment_method")
    total = get_cart_value(cart)

    if method == "k":
        # karta
        time.sleep(1)
        save_cart([])
        flash(f"Płatność kartą zaakceptowana. Do zapłaty: {total} zł. Drukowanie biletów... Dziękujemy!", "success")
    elif method == "g":
        try:
            paid_str = request.form.get("paid_amount", "0").replace(",", ".")
            paid = float(paid_str)
            if paid < total:
                flash(f"Wrzucono za mało! Do zapłaty {total} zł, wrzucono {paid} zł", "error")
                return redirect(url_for("index"))
            change = round(paid - total, 2)
            save_cart([])
            if change > 0:
                flash(f"Zapłacono {paid} zł. Reszta: {change} zł. Drukowanie biletów... Dziękujemy!", "success")
            else:
                flash(f"Zapłacono dokładnie {total} zł. Drukowanie biletów... Dziękujemy!", "success")
        except ValueError:
            flash("Nieprawidłowa kwota!", "error")
            return redirect(url_for("index"))
    elif method == "b":
        blik = request.form.get("blik_code", "")
        if len(blik) != 6 or not blik.isdigit():
            flash("Płatność BLIK nie powiodła się - kod musi mieć 6 cyfr!", "error")
            return redirect(url_for("index"))
        time.sleep(1)
        save_cart([])
        flash(f"Płatność BLIK {blik} zaakceptowana. Do zapłaty: {total} zł. Drukowanie biletów... Dziękujemy!", "success")
    else:
        flash("Wybierz metodę płatności!", "error")
        return redirect(url_for("index"))

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
