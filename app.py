import json
import os
from flask import Flask, redirect, render_template_string, request, session, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'syria_k9_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_FILE = 'attendance_data.json'

def create_default_icon():
    os.makedirs('static', exist_ok=True)
    icon_path = 'static/icon.png'
    if not os.path.exists(icon_path):
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00$\x00\x00\x00$\x08\x06\x00\x00\x00p\n\xbe\xfa\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x1fIDATx\x9cc\xfc\xff\xff?@\x03\x06\x18\x0c(\x10\x84\x82\x81\x81\x81!\x8c\x02\x00\xcaV\x05G\xfb\xef\x8f\xf1\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(icon_path, 'wb') as f:
            f.write(png_data)

create_default_icon()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"staff": [], "units": [], "attendance": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

html_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syria K9 Unit - النظام الميداني</title>
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='icon.png') }}">
    <link rel="apple-touch-icon" href="{{ url_for('static', filename='icon.png') }}">
    <style>
        body { background-color: #0d1117; color: #ffffff; font-family: Tahoma, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 550px; margin: 20px auto; background: #161b22; padding: 20px; border-radius: 12px; border: 2px solid #cc0000; box-shadow: 0 0 20px rgba(204,0,0,0.4); }
        .logo-box { font-size: 20px; font-weight: bold; color: #ff1a1a; text-align: center; margin-bottom: 15px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        input, select, textarea { width: 100%; padding: 10px; margin: 8px 0; background: #0d1117; border: 1px solid #333; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #cc0000; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 8px; }
        button:hover { background: #990000; }
        table { width: 100%; margin-top: 15px; border-collapse: collapse; text-align: center; font-size: 13px; }
        th, td { border: 1px solid #333; padding: 8px; }
        th { background: #cc0000; color: white; }
        .nav-links { display: flex; gap: 5px; margin-bottom: 15px; }
        .nav-links a { flex: 1; padding: 8px; background: #21262d; color: #fff; text-align: center; text-decoration: none; border-radius: 5px; font-size: 13px; }
        .nav-links a:hover, .nav-links a.active { background: #cc0000; }
        .schedule-box { background: #0d1117; padding: 10px; border-radius: 6px; border: 1px solid #333; text-align: right; margin-top: 10px; font-size: 13px; line-height: 1.6; }
        .logout { background: #21262d; margin-top: 15px; display: block; color: #8b949e; text-align: center; text-decoration: none; padding: 8px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-box">SYRIA K9 UNIT - النظام الميداني</div>
        
        {% if not session.get('user') %}
            <p style="text-align: center; color: #8b949e;">تسجيل الدخول للنظام</p>
            <form method="POST" action="/login">
                <label style="font-size:13px; color:#8b949e;">اختر نوع الحساب:</label>
                <select name="role" required>
                    <option value="staff">موظف (تسجيل حضور فقط)</option>
                    <option value="admin">مسؤول (Admin - صلاحيات كاملة)</option>
                </select>
                <input type="text" name="identifier" placeholder="اسم المستخدم أو المعرّف" required>
                <input type="password" name="password" placeholder="كلمة المرور" required>
                <button type="submit">دخول</button>
            </form>
        {% else %}
            <div style="background: #21262d; padding: 6px 10px; border-radius: 5px; font-size: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; color: #8b949e;">
                <span>المستخدم: <b>{{ session.get('user') }}</b></span>
                <span>الحالة: <b style="color: {% if session.get('is_admin') %}#2ecc71{% else %}#3498db{% endif %};">{% if session.get('is_admin') %}مسؤول نظام{% else %}موظف ميداني{% endif %}</b></span>
            </div>

            <div class="nav-links">
                <a href="/?tab=attendance" {% if active_tab == 'attendance' %}class="active"{% endif %}>الحضور</a>
                <a href="/?tab=units" {% if active_tab == 'units' %}class="active"{% endif %}>الوحدات</a>
                <a href="/?tab=schedule" {% if active_tab == 'schedule' %}class="active"{% endif %}>البرنامج</a>
                {% if session.get('is_admin') %}
                <a href="/?tab=admin" {% if active_tab == 'admin' %}class="active"{% endif %}>الإدارة</a>
                {% endif %}
            </div>

            {% if active_tab == 'attendance' %}
                <h3>تسجيل الحضور والغياب الميداني</h3>
                <form method="POST" action="/attendance" enctype="multipart/form-data" onsubmit="getGPS(event, this)">
                    <label>اختر اسمك:</label>
                    <select name="name" required>
                        <option value="">-- اختر --</option>
                        {% for staff in data.staff %}
                        <option value="{{ staff }}">{{ staff }}</option>
                        {% endfor %}
                    </select>
                    
                    <label>الحالة:</label>
                    <select name="status" id="statusSelect" onchange="toggleReason(this)">
                        <option value="حاضر">حاضر</option>
                        <option value="غائب">غائب</option>
                        <option value="غياب مبرر">غياب مبرر (مع تقرير)</option>
                    </select>

                    <div id="reasonBox" style="display:none;">
                        <label>سبب الغياب أو المبرر:</label>
                        <textarea name="reason" placeholder="أدخل التفاصيل..."></textarea>
                        <label>صورة التقرير / الإثبات:</label>
                        <input type="file" name="report_image" accept="image/*">
                    </div>

                    <input type="hidden" name="gps" id="gpsInput">
                    <button type="submit">إرسال تسجيل الحضور</button>
                </form>

                <!-- السجلات تظهر للمسؤول فقط -->
                {% if session.get('is_admin') %}
                <h3 style="margin-top: 25px; border-top: 1px solid #333; padding-top: 15px; color: #ff1a1a;">سجلات الحضور (خاص بالمسؤول)</h3>
                <table>
                    <tr>
                        <th>الاسم</th>
                        <th>الحالة</th>
                        <th>الموقع (GPS)</th>
                        <th>التفاصيل</th>
                    </tr>
                    {% for rec in data.attendance %}
                    <tr>
                        <td>{{ rec.name }}</td>
                        <td style="color: {% if rec.status == 'حاضر' %}#2ecc71{% else %}#e74c3c{% endif %};">{{ rec.status }}</td>
                        <td style="font-size: 11px;">{{ rec.gps }}</td>
                        <td>
                            {% if rec.reason %}{{ rec.reason }}<br>{% endif %}
                            {% if rec.image %}<a href="/{{ rec.image }}" target="_blank" style="color: #3498db;">[عرض التقرير]</a>{% endif %}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="4" style="color: #8b949e;">لا توجد سجلات مسجلة بعد</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p style="text-align: center; color: #8b949e; margin-top: 20px; font-size: 13px;">تم إرسال حضورك بنجاح. سجلات الزملاء خاصة بالمسؤولين فقط.</p>
                {% endif %}

            {% elif active_tab == 'units' %}
                <h3>إدارة الوحدات الفعالة</h3>
                
                {% if session.get('is_admin') %}
                <form method="POST" action="/add_unit" style="background: #0d1117; padding: 12px; border-radius: 6px; border: 1px solid #333; margin-bottom: 15px;">
                    <label style="color: #8b949e; font-size: 13px;">اسم الوحدة / العنصر:</label>
                    <input type="text" name="unit_name" placeholder="أدخل اسم الوحدة هنا..." required>
                    <label style="color: #8b949e; font-size: 13px;">الملاحظات والتفاصيل:</label>
                    <textarea name="unit_notes" placeholder="أدخل الملاحظات والمهام..."></textarea>
                    <button type="submit">إضافة الوحدة للقائمة</button>
                </form>
                {% endif %}

                <table>
                    <tr><th>اسم الوحدة</th><th>الملاحظات</th></tr>
                    {% for u in data.units %}
                    <tr>
                        <td style="font-weight: bold; color: #ff1a1a;">{{ u.name }}</td>
                        <td style="text-align: right; padding: 10px;">{{ u.notes }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="2" style="color: #8b949e;">لا توجد وحدات مضافة حتى الآن</td>
                    </tr>
                    {% endfor %}
                </table>

            {% elif active_tab == 'schedule' %}
                <h3>البرنامج اليومي الشامل (07:00 ص - 07:00 م)</h3>
                <div class="schedule-box">
                    <b>07:00 ص:</b> تفقد عام ونظافة أماكن الإيواء.<br>
                    <b>08:00 ص:</b> الوجبة الصباحية وتفتيش الحالة الصحية.<br>
                    <b>09:30 ص:</b> تدريبات الطاعة واللياقة البدنية الميدانية.<br>
                    <b>12:00 م:</b> فترة راحة واستشفاء للفرق والوحدات.<br>
                    <b>03:00 بظ:</b> تدريبات التمشيط والاقتفاء المتقدمة.<br>
                    <b>05:30 بظ:</b> الوجبة المسائية والعناية الطبية الوقائية.<br>
                    <b>06:30 بظ:</b> مراجعة اليوم وتسليم الوردية والاستطلاع الليلي حتى 07:00 م.
                </div>

            {% elif active_tab == 'admin' and session.get('is_admin') %}
                <h3>لوحة إدارة الموظفين</h3>
                <form method="POST" action="/add_staff">
                    <input type="text" name="staff_name" placeholder="اسم الموظف الجديد" required>
                    <button type="submit">إضافة موظف للقائمة</button>
                </form>
                <table>
                    <tr><th>الموظفون المسجلون</th></tr>
                    {% for s in data.staff %}
                    <tr><td>{{ s }}</td></tr>
                    {% endfor %}
                </table>
            {% endif %}

            <a href="/logout" class="logout">تسجيل الخروج</a>
        {% endif %}
    </div>

    <script>
        function toggleReason(select) {
            let box = document.getElementById('reasonBox');
            box.style.display = (select.value === 'غياب مبرر') ? 'block' : 'none';
        }
        function getGPS(e, form) {
            e.preventDefault();
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    let lat = position.coords.latitude.toFixed(4);
                    let lon = position.coords.longitude.toFixed(4);
                    document.getElementById('gpsInput').value = lat + ", " + lon;
                    form.submit();
                }, function(error) {
                    document.getElementById('gpsInput').value = "غير متوفر (تم الرفض)";
                    form.submit();
                });
            } else {
                document.getElementById('gpsInput').value = "غير مدعوم";
                form.submit();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    data = load_data()
    active_tab = request.args.get('tab', 'attendance')
    return render_template_string(html_template, data=data, active_tab=active_tab)

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    identifier = request.form.get('identifier')
    session['user'] = identifier
    if role == 'admin':
        session['is_admin'] = True
    else:
        session['is_admin'] = False
    return redirect(url_for('index'))

@app.route('/attendance', methods=['POST'])
def attendance():
    if 'user' in session:
        data = load_data()
        name = request.form.get('name')
        status = request.form.get('status')
        gps = request.form.get('gps', 'غير محدد')
        reason = request.form.get('reason', '')
        
        image_path = ""
        if 'report_image' in request.files:
            file = request.files['report_image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"static/uploads/{filename}"

        data['attendance'].insert(0, {
            'name': name,
            'status': status,
            'gps': gps,
            'reason': reason,
            'image': image_path,
            'user': session['user']
        })
        save_data(data)
    return redirect(url_for('index', tab='attendance'))

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if session.get('is_admin'):
        data = load_data()
        name = request.form.get('staff_name')
        if name and name not in data['staff']:
            data['staff'].append(name)
            save_data(data)
    return redirect(url_for('index', tab='admin'))

@app.route('/add_unit', methods=['POST'])
def add_unit():
    if session.get('is_admin'):
        data = load_data()
        name = request.form.get('unit_name')
        notes = request.form.get('unit_notes')
        if name:
            data['units'].append({'name': name, 'notes': notes})
            save_data(data)
    return redirect(url_for('index', tab='units'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == 'main' or __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
