const api = "/api";
let currentCustId = null;

// Tarih formatı: YYYY-MM-DD -> GG/AA/YYYY
function formatDate(dateStr) {
    if (!dateStr) return '---';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

// Ay formatı: YYYY-MM -> AA/YYYY
function formatMonth(monthStr) {
    if (!monthStr) return '---';
    const parts = monthStr.split('-');
    if (parts.length !== 2) return monthStr;
    return `${parts[1]}/${parts[0]}`;
}
class UIManager {
    show(v) {
        document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
        const t = document.getElementById('v-' + v); if (t) t.classList.add('active');
        if (v === 'list') this.load(); if (v === 'finance') this.loadFinance();
        if (v === 'reminders') { this.loadReminders(); this.switchTab('main'); }
        if (v === 'users') this.loadUsers();
        if (v === 'add') document.getElementById('add-date').valueAsDate = new Date();
        this.updateStats();
    }
    async load() {
        const q = encodeURIComponent(document.getElementById('q').value);
        const res = await fetch(`${api}/customers?q=${q}`);
        const data = await res.json();
        const container = document.getElementById('l-b');
        container.innerHTML = '';
        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-slate-50 cursor-pointer';
            tr.onclick = () => this.details(c.id);
            tr.innerHTML = `
                <td class="p-4 font-bold text-slate-700"></td>
                <td class="p-4 text-slate-500"></td>
                <td class="p-4 text-xs font-medium text-slate-400"></td>
                <td class="p-4 text-right text-sky-600 font-bold">Detay →</td>
            `;
            tr.cells[0].textContent = c.name;
            tr.cells[1].textContent = c.phone;
            tr.cells[2].textContent = c.district;
            container.appendChild(tr);
        });
    }
    async details(id) {
        try {
            const c = await (await fetch(`${api}/customers/${id}`)).json();
            currentCustId = id;
            document.getElementById('d-title').textContent = c.name;
            document.getElementById('d-phone').textContent = c.phone || "---";
            document.getElementById('d-district').textContent = c.district || "---";
            document.getElementById('d-address').textContent = c.address || "---";
            const h = await (await fetch(`${api}/customers/${id}/history`)).json();
            const latestBrand = h.length > 0 ? (h[0].brand || "---") : "---";
            document.getElementById('d-brand').textContent = latestBrand;

            const container = document.getElementById('d-b');
            container.innerHTML = '';
            h.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="p-4 text-xs font-bold text-slate-400"></td>
                    <td class="p-4 font-bold text-sky-600"></td>
                    <td class="p-4 font-bold text-slate-700"></td>
                    <td class="p-4 font-black text-slate-500"></td>
                    <td class="p-4 text-right">
                        <span class="px-3 py-1 rounded-lg text-[10px] font-black"></span>
                    </td>
                `;
                tr.cells[0].textContent = formatDate(r.date);
                tr.cells[1].textContent = r.brand || '---';
                tr.cells[2].textContent = r.job;
                tr.cells[3].textContent = `${r.paid_fee}/${r.total_fee} TL`;
                const status = tr.cells[4].querySelector('span');
                status.textContent = r.is_paid ? 'ÖDENDİ' : 'BORÇ';
                status.className += r.is_paid ? ' bg-green-100 text-green-700' : ' bg-amber-100 text-amber-700';
                container.appendChild(tr);
            });
            this.show('det');
        } catch (e) { alert("Detay hatası!"); }
    }
    async editMode() {
        const c = await (await fetch(`${api}/customers/${currentCustId}`)).json();
        document.getElementById('edit-name').value = c.name;
        document.getElementById('edit-phone').value = c.phone;
        document.getElementById('edit-district').value = c.district;
        document.getElementById('edit-address').value = c.address;
        this.show('edit');
    }
    async updateCust(e) {
        e.preventDefault();
        const res = await fetch(`${api}/customers/${currentCustId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(e.target))) });
        const r = await res.json();
        if (res.ok) { alert("Güncellendi!"); currentCustId = r.new_id; this.details(currentCustId); } else { alert(r.detail); }
    }
    async deleteCust() {
        if (confirm("Silmek istediğinize emin misiniz?")) { await fetch(`${api}/customers/${currentCustId}`, { method: 'DELETE' }); this.show('list'); }
    }
    async loadFinance() {
        const data = await (await fetch(`${api}/finance/monthly`)).json();
        const container = document.getElementById('f-b');
        container.innerHTML = '';
        data.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td class="p-4 font-black text-slate-700"></td><td class="p-4 text-emerald-600 font-black"></td>';
            tr.cells[0].textContent = formatMonth(f.month);
            tr.cells[1].textContent = `${f.total.toLocaleString()} TL`;
            container.appendChild(tr);
        });
    }
    async collect(id) {
        if (confirm("Ödeme alındı mı?")) { await fetch(`${api}/records/${id}/collect`, { method: 'POST' }); this.loadReminders(); this.updateStats(); }
    }
    async openWhatsapp(phone, type, name, amount) {
        if (!phone || phone.length < 10) return alert("Geçerli bir telefon numarası yok!");
        let p = phone.replace(/\D/g, '');
        if (p.startsWith('0')) p = p.substring(1);
        if (!p.startsWith('90')) p = '90' + p;

        let msg = "";
        if (type === 'bakim') msg = `Sayın ${name}, kombi bakım zamanınız gelmiştir. Randevu oluşturmak için lütfen iletişime geçiniz.`;
        if (type === 'borc') msg = `Sayın ${name}, ${amount} TL tutarındaki bakiyeniz için ödeme yapmanızı rica ederiz.`;
        if (type === 'genel') msg = `Sayın ${name}, `;

        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.open_external(`https://wa.me/${p}?text=${encodeURIComponent(msg)}`);
        } else {
            window.open(`https://wa.me/${p}?text=${encodeURIComponent(msg)}`, '_blank');
        }
    }

    async loadReminders() {
        const data = await (await fetch(`${api}/reminders`)).json();
        const today = new Date().toISOString().split('T')[0];
        const rContainer = document.getElementById('r-b');
        rContainer.innerHTML = '';
        data.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="p-4 font-bold text-slate-700"></td>
                <td class="p-4 text-slate-500"></td>
                <td class="p-4 font-black"></td>
                <td class="p-4 text-right flex justify-end items-center gap-2">
                    <button class="bg-green-500 text-white px-3 py-1 rounded-lg text-[10px] font-bold hover:bg-green-600">🔔 Hatırlat</button>
                    <span class="px-3 py-1 rounded-lg text-[10px] font-black"></span>
                </td>
            `;
            tr.cells[0].textContent = r.name;
            tr.cells[1].textContent = r.phone;
            tr.cells[2].textContent = formatDate(r.reminder_date);
            tr.cells[2].className += r.reminder_date < today ? ' text-red-600' : ' text-emerald-600';

            const btn = tr.cells[3].querySelector('button');
            btn.onclick = () => this.openWhatsapp(r.phone, 'bakim', r.name, 0);

            const status = tr.cells[3].querySelector('span');
            status.textContent = r.reminder_date < today ? 'GEÇMİŞ' : 'YAKIN';
            status.className += r.reminder_date < today ? ' bg-red-100 text-red-600' : ' bg-emerald-100 text-emerald-600';
            rContainer.appendChild(tr);
        });

        const unpaid = await (await fetch(`${api}/finance/unpaid`)).json();
        const uContainer = document.getElementById('u-b');
        uContainer.innerHTML = '';
        unpaid.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="p-4 font-bold"></td>
                <td class="p-4 font-black text-amber-700"></td>
                <td class="p-4 text-right flex justify-end items-center gap-2">
                    <button class="bg-green-500 text-white px-3 py-1 rounded-lg text-[10px] font-bold hover:bg-green-600">💬 Talep Et</button>
                    <button class="bg-emerald-600 text-white px-4 py-2 rounded-xl text-xs font-black">ÖDEME ALINDI</button>
                </td>
            `;
            tr.cells[0].textContent = r.name;
            tr.cells[1].textContent = `${r.debt.toLocaleString()} TL`;

            const btns = tr.cells[2].querySelectorAll('button');
            btns[0].onclick = () => this.openWhatsapp(r.phone, 'borc', r.name, r.debt.toLocaleString());
            btns[1].onclick = () => this.collect(r.id);
            uContainer.appendChild(tr);
        });

        const debtTabBtn = document.getElementById('tab-btn-debt');
        if (unpaid.length > 0) {
            debtTabBtn.classList.remove('hidden');
        } else {
            debtTabBtn.classList.add('hidden');
            if (!document.getElementById('tab-content-debt').classList.contains('hidden')) {
                this.switchTab('main');
            }
        }
    }
    switchTab(t) {
        ['main', 'debt'].forEach(x => {
            document.getElementById('tab-content-' + x).classList.add('hidden');
            const btn = document.getElementById('tab-btn-' + x);
            btn.classList.remove('border-sky-500', 'text-sky-600', 'border-amber-500', 'text-amber-600');
            btn.classList.add('border-transparent', 'text-slate-400');
        });
        document.getElementById('tab-content-' + t).classList.remove('hidden');
        const activeBtn = document.getElementById('tab-btn-' + t);
        activeBtn.classList.remove('border-transparent', 'text-slate-400');
        if (t === 'main') activeBtn.classList.add('border-sky-500', 'text-sky-600');
        if (t === 'debt') activeBtn.classList.add('border-amber-500', 'text-amber-600');
    }
    async updateStats() {
        const d = await (await fetch(`${api}/finance/stats`)).json();
        document.getElementById('stat-m').innerText = (d.aylik || 0).toLocaleString() + " TL";
        document.getElementById('stat-r').innerText = (d.alinacak || 0).toLocaleString() + " TL";
    }
    async save(e) {
        e.preventDefault();
        const res = await fetch(`${api}/customers`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(new FormData(e.target))) });
        if (res.ok) { alert("Kaydedildi!"); this.show('list'); e.target.reset(); } else { alert("Hata: " + (await res.json()).detail); }
    }
    async upload(input) {
        const fd = new FormData(); fd.append('file', input.files[0]);
        const res = await fetch(`${api}/import-excel`, { method: 'POST', body: fd });
        const d = await res.json(); alert(`${d.count} başarılı.`); this.load(); input.value = "";
    }
    async telegramBackup() {
        if (!confirm("Veritabanı yedeğini Telegram botuna göndermek istiyor musunuz?")) return;

        try {
            const res = await fetch(`${api}/backup/telegram`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                alert("✅ " + data.message);
            } else {
                alert("❌ Hata: " + (data.detail || "Yedek gönderilemedi"));
            }
        } catch (e) {
            alert("❌ Bağlantı hatası!");
        }
    }
    async createUser(e) {
        e.preventDefault();
        const username = document.getElementById('new-username').value;
        const name = document.getElementById('new-name').value;
        const password = document.getElementById('new-password').value;
        const msgEl = document.getElementById('user-msg');

        try {
            const res = await fetch(`${api}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, name, password })
            });

            if (res.ok) {
                msgEl.innerText = '✅ Kullanıcı başarıyla oluşturuldu!';
                msgEl.className = 'text-center mt-4 text-sm text-green-600';
                msgEl.classList.remove('hidden');
                document.getElementById('new-username').value = '';
                document.getElementById('new-name').value = '';
                document.getElementById('new-password').value = '';
            } else {
                const err = await res.json();
                msgEl.innerText = '❌ ' + (err.detail || 'Hata oluştu');
                msgEl.className = 'text-center mt-4 text-sm text-red-600';
                msgEl.classList.remove('hidden');
            }
        } catch (err) {
            msgEl.innerText = '❌ Bağlantı hatası';
            msgEl.className = 'text-center mt-4 text-sm text-red-600';
            msgEl.classList.remove('hidden');
        }
    }
    async logout() {
        await fetch(`${api}/auth/logout`, { method: 'POST' });
        window.location.href = '/login';
    }
    async changePassword(e) {
        e.preventDefault();
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password-change').value;
        const msgEl = document.getElementById('password-msg');

        try {
            const res = await fetch(`${api}/auth/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
            });

            if (res.ok) {
                msgEl.innerText = '✅ Şifre başarıyla değiştirildi!';
                msgEl.className = 'text-center mt-4 text-sm text-green-600';
                msgEl.classList.remove('hidden');
                document.getElementById('current-password').value = '';
                document.getElementById('new-password-change').value = '';
            } else {
                const err = await res.json();
                msgEl.innerText = '❌ ' + (err.detail || 'Hata oluştu');
                msgEl.className = 'text-center mt-4 text-sm text-red-600';
                msgEl.classList.remove('hidden');
            }
        } catch (err) {
            msgEl.innerText = '❌ Bağlantı hatası';
            msgEl.className = 'text-center mt-4 text-sm text-red-600';
            msgEl.classList.remove('hidden');
        }
    }
    async loadUsers() {
        try {
            const res = await fetch(`${api}/auth/users`);
            if (!res.ok) return;
            const users = await res.json();
            const container = document.getElementById('users-list');
            container.innerHTML = '';
            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-50';
                tr.innerHTML = `
                    <td class="p-4 font-bold text-slate-700"></td>
                    <td class="p-4 text-slate-600"></td>
                    <td class="p-4 text-xs text-slate-400"></td>
                    <td class="p-4 text-right">
                        <button class="px-3 py-1 bg-red-100 text-red-700 rounded-lg text-xs font-bold hover:bg-red-200">
                            🗑️ Sil
                        </button>
                    </td>
                `;
                tr.cells[0].textContent = u.username;
                tr.cells[1].textContent = u.name || '-';
                tr.cells[2].textContent = u.created_at ? formatDate(u.created_at.split(' ')[0]) : '-';

                const btn = tr.cells[3].querySelector('button');
                btn.onclick = () => this.deleteUser(u.id, u.username);
                container.appendChild(tr);
            });
        } catch (e) { console.error('Users yüklenemedi:', e); }
    }
    async deleteUser(userId, username) {
        if (!confirm(`"${username}" kullanıcısını silmek istediğinize emin misiniz? Tüm müşterileri ve kayıtları da silinecek!`)) return;

        try {
            const res = await fetch(`${api}/auth/users/${userId}`, { method: 'DELETE' });
            if (res.ok) {
                alert('Kullanıcı silindi!');
                this.loadUsers();
            } else {
                const err = await res.json();
                alert('Hata: ' + (err.detail || 'Silinemedi'));
            }
        } catch (e) { alert('Bağlantı hatası!'); }
    }
}
const ui = new UIManager();
window.onload = async () => {
    // Aktif kullanıcı bilgisini al
    try {
        const authRes = await fetch(`${api}/auth/check`);
        const authData = await authRes.json();
        if (authData.authenticated) {
            document.getElementById('current-user').textContent = '👤 ' + (authData.name || authData.username);
        }
    } catch (e) { }
    ui.show('list');
    ui.updateStats();
};
