from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def get_db_connection():
    conn = sqlite3.connect('menu.db')
    conn.row_factory = sqlite3.Row
    return conn

# ----------- Customer Routes -----------
@app.route('/')
def menu():
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM menu WHERE stock > 0').fetchall()
    conn.close()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/complete')
def complete():
    return render_template('complete.html')

# ----------- Admin Routes -----------
@app.route('/admin/orders')
def admin_orders():
    conn = get_db_connection()
    orders = conn.execute("""
        SELECT o.id, o.table_number, o.status, o.created_at, SUM(m.price * oi.quantity) as total_price
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN menu m ON oi.menu_id = m.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/menu', methods=['GET', 'POST'])
def admin_menu():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        stock = request.form['stock']
        conn.execute('INSERT INTO menu (name, price, stock) VALUES (?, ?, ?)', (name, price, stock))
        conn.commit()
        return redirect(url_for('admin_menu'))
    
    menu_items = conn.execute('SELECT * FROM menu').fetchall()
    conn.close()
    return render_template('admin_menu.html', menu_items=menu_items)

# ----------- API Endpoints -----------
@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.get_json()
    table_number = data['table_number']
    cart = data['cart'] # cart is a list of {'id': menu_id, 'quantity': ...}

    conn = get_db_connection()
    try:
        # 1. Create an order
        cur = conn.cursor()
        cur.execute('INSERT INTO orders (table_number) VALUES (?)', (table_number,))
        order_id = cur.lastrowid

        # 2. Create order items and update stock
        for item in cart:
            # Check stock
            menu_item = conn.execute('SELECT stock FROM menu WHERE id = ?', (item['id'],)).fetchone()
            if menu_item['stock'] < item['quantity']:
                conn.rollback()
                return jsonify({'success': False, 'message': f'{menu_item["name"]} 재고 부족'}), 400

            cur.execute('INSERT INTO order_items (order_id, menu_id, quantity) VALUES (?, ?, ?)', 
                        (order_id, item['id'], item['quantity']))
            cur.execute('UPDATE menu SET stock = stock - ? WHERE id = ?', (item['quantity'], item['id']))

        conn.commit()

        # Notify admin page
        new_order = conn.execute("""
            SELECT o.id, o.table_number, o.status, o.created_at, SUM(m.price * oi.quantity) as total_price
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu m ON oi.menu_id = m.id
            WHERE o.id = ? GROUP BY o.id
        """, (order_id,)).fetchone()
        
        socketio.emit('new_order', {
            'id': new_order['id'],
            'table_number': new_order['table_number'],
            'status': new_order['status'],
            'total_price': new_order['total_price'],
            'created_at': new_order['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        })

        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data['status']
    
    conn = get_db_connection()
    conn.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()

    socketio.emit('status_update', {'order_id': order_id, 'status': new_status})
    return jsonify({'success': True})

@app.route('/api/menu/<int:menu_id>', methods=['POST'])
def update_menu_item(menu_id):
    data = request.form
    conn = get_db_connection()
    conn.execute('UPDATE menu SET name=?, price=?, stock=? WHERE id=?', 
                 (data['name'], data['price'], data['stock'], menu_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_menu'))

# ----------- SocketIO Events -----------
@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, debug=True)