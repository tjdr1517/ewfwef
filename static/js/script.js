document.addEventListener('DOMContentLoaded', () => {
    const cart = JSON.parse(localStorage.getItem('cart')) || {};

    function saveCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
    }

    function addToCart(itemId, name, price) {
        if (cart[itemId]) {
            cart[itemId].quantity++;
        } else {
            cart[itemId] = { name, price, quantity: 1 };
        }
        saveCart();
        alert(`${name}이(가) 장바구니에 추가되었습니다.`);
    }

    // --- Menu Page ---
    if (document.querySelector('.menu-container')) {
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', () => {
                const menuItem = button.closest('.menu-item');
                const id = menuItem.dataset.id;
                const name = menuItem.dataset.name;
                const price = parseInt(menuItem.dataset.price);
                addToCart(id, name, price);
            });
        });
    }

    // --- Cart Page ---
    if (document.getElementById('cart-items')) {
        const cartItemsContainer = document.getElementById('cart-items');
        let totalPrice = 0;
        for (const id in cart) {
            const item = cart[id];
            const itemElement = document.createElement('div');
            itemElement.innerHTML = `<p>${item.name} - ${item.price}원 x ${item.quantity}</p>`;
            cartItemsContainer.appendChild(itemElement);
            totalPrice += item.price * item.quantity;
        }
        document.getElementById('total-price').textContent = totalPrice;
    }

    // --- Checkout Page ---
    if (document.getElementById('checkout-form')) {
        document.getElementById('checkout-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const tableNumber = document.getElementById('table_number').value;
            const cartForApi = Object.keys(cart).map(id => ({ id: parseInt(id), quantity: cart[id].quantity }));

            const response = await fetch('/api/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ table_number: tableNumber, cart: cartForApi })
            });

            if (response.ok) {
                localStorage.removeItem('cart');
                window.location.href = '/complete';
            } else {
                const result = await response.json();
                alert(`주문 실패: ${result.message}`);
            }
        });
    }

    // --- Admin Orders Page ---
    if (document.getElementById('orders-table-body')) {
        const socket = io();

        socket.on('connect', () => console.log('Socket.IO Connected'));

        socket.on('new_order', (order) => {
            const tableBody = document.getElementById('orders-table-body');
            const newRow = document.createElement('tr');
            newRow.id = `order-${order.id}`;
            newRow.innerHTML = `
                <td>${order.id}</td>
                <td>${order.table_number}</td>
                <td>${order.created_at}</td>
                <td>${order.total_price}원</td>
                <td class="status">${order.status}</td>
                <td>
                    <select class="status-changer" data-order-id="${order.id}">
                        <option value="접수" ${order.status === '접수' ? 'selected' : ''}>접수</option>
                        <option value="조리 중" ${order.status === '조리 중' ? 'selected' : ''}>조리 중</option>
                        <option value="완료" ${order.status === '완료' ? 'selected' : ''}>완료</option>
                    </select>
                </td>
            `;
            tableBody.prepend(newRow);
        });

        socket.on('status_update', (data) => {
            const orderRow = document.getElementById(`order-${data.order_id}`);
            if (orderRow) {
                orderRow.querySelector('.status').textContent = data.status;
            }
        });

        document.body.addEventListener('change', async (e) => {
            if (e.target.classList.contains('status-changer')) {
                const orderId = e.target.dataset.orderId;
                const newStatus = e.target.value;
                await fetch(`/api/order/${orderId}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
            }
        });
    }
});
