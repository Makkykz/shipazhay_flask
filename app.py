from flask import Flask, render_template, abort, request, redirect, url_for
import json
import os
import datetime # Для добавления даты и времени бронирования
import uuid     # Для генерации уникального ID бронирования

app = Flask(__name__)

# --- ЗАГРУЗКА ДАННЫХ О ШИПАЖАЯХ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(BASE_DIR, 'shipazhays.json')
BOOKINGS_JSON_FILE_PATH = os.path.join(BASE_DIR, 'bookings.json') # Файл для бронирований

def load_data_from_json(file_path):
    print(f"--- Пытаюсь загрузить данные из: {file_path} ---")
    if not os.path.exists(file_path):
        print(f"ОШИБКА: Файл {file_path} НЕ НАЙДЕН.")
        return []
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"--- ДАННЫЕ ИЗ {os.path.basename(file_path)} УСПЕШНО ЗАГРУЖЕНЫ (длина: {len(data)}) ---")
            return data
    except json.JSONDecodeError as e:
        print(f"ОШИБКА: Не удалось декодировать JSON из файла {file_path}.")
        print(f"Детали ошибки JSONDecodeError: {e}")
        return []
    except Exception as e:
        print(f"ОШИБКА: Произошла непредвиденная ошибка при чтении файла {file_path}.")
        print(f"Детали ошибки: {e}")
        return []

all_shipazhays_data = load_data_from_json(JSON_FILE_PATH)

def save_booking(new_booking):
    bookings = load_data_from_json(BOOKINGS_JSON_FILE_PATH)
    bookings.append(new_booking)
    try:
        with open(BOOKINGS_JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(bookings, f, ensure_ascii=False, indent=4)
            print("--- БРОНИРОВАНИЕ УСПЕШНО СОХРАНЕНО ---")
            return True
    except Exception as e:
        print(f"ОШИБКА: Не удалось сохранить бронирование в файл {BOOKINGS_JSON_FILE_PATH}.")
        print(f"Детали ошибки: {e}")
        return False

# --- МАРШРУТЫ ---
@app.route('/')
def home():
    page_title = "Добро пожаловать в Шипажай!"
    featured_shipazhays = all_shipazhays_data[:2] if all_shipazhays_data else []
    return render_template('index.html', title=page_title, shipazhays=featured_shipazhays)

@app.route('/about')
def about():
    return render_template('about.html', title="О Шипажаях Казахстана")

@app.route('/shipazhai/')
def shipazhay_list():
    page_title = "Все Шипажаи Казахстана"
    return render_template('shipazhay_list.html', title=page_title, shipazhays=all_shipazhays_data)

@app.route('/shipazhai/<slug>/')
def shipazhay_detail(slug):
    shipazhay_found = None
    if all_shipazhays_data:
        for s in all_shipazhays_data:
            if s.get('slug') == slug:
                shipazhay_found = s
                break
    
    if shipazhay_found is None:
        if not all_shipazhays_data:
            return "Ошибка: не удалось загрузить данные о шипажаях. Проверьте файл shipazhays.json и вывод сервера.", 500
        abort(404) 

    page_title = shipazhay_found.get('name', 'Детали Шипажая')
    return render_template('shipazhay_detail.html', title=page_title, shipazhay=shipazhay_found)

@app.route('/contact/')
def contact():
    page_title = "Свяжитесь с нами"
    return render_template('contact.html', title=page_title)

# --- МАРШРУТЫ ДЛЯ БРОНИРОВАНИЯ ---
@app.route('/booking/', methods=['GET'])
@app.route('/booking/<slug>/', methods=['GET']) # slug шипажая для предзаполнения
def booking_form(slug=None):
    page_title = "Оформление заявки на бронирование"
    shipazhay_name_for_form = None

    if slug and all_shipazhays_data:
        for s in all_shipazhays_data:
            if s.get('slug') == slug:
                shipazhay_name_for_form = s.get('name')
                break
    
    # Передаем все шипажаи для выпадающего списка, если конкретный не выбран или не найден
    available_shipazhays = all_shipazhays_data if all_shipazhays_data else []
    
    return render_template('booking.html', 
                           title=page_title, 
                           shipazhay_name=shipazhay_name_for_form,
                           all_shipazhays_for_booking=available_shipazhays)

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if request.method == 'POST':
        booking_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Более читаемый формат даты
            'shipazhay_name': request.form.get('shipazhay_name'),
            'full_name': request.form.get('full_name'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email', ''),
            'date_from': request.form.get('date_from'),
            'date_to': request.form.get('date_to'),
            'adults': request.form.get('adults'),
            'children': request.form.get('children', '0'),
            'comments': request.form.get('comments', '')
        }
        
        # Простая валидация (можно расширить)
        if not all([booking_data['shipazhay_name'], booking_data['full_name'], booking_data['phone'], booking_data['date_from'], booking_data['date_to'], booking_data['adults']]):
            # Можно передать сообщение об ошибке обратно на форму бронирования
            # Для простоты пока просто перенаправляем с сообщением (в реальном приложении лучше)
            print("ОШИБКА: Не все обязательные поля бронирования заполнены.")
            return redirect(url_for('booking_form')) # Можно добавить параметр с ошибкой

        if save_booking(booking_data):
            return redirect(url_for('booking_confirmation', booking_id=booking_data['id']))
        else:
            # Обработка ошибки сохранения (например, показать страницу с ошибкой)
            return "Произошла ошибка при сохранении вашего бронирования. Пожалуйста, попробуйте позже.", 500
            
    return redirect(url_for('home'))

@app.route('/booking_confirmation/<booking_id>')
def booking_confirmation(booking_id):
    all_bookings = load_data_from_json(BOOKINGS_JSON_FILE_PATH)
    current_booking = None
    if all_bookings:
        for bk in all_bookings:
            if bk.get('id') == booking_id:
                current_booking = bk
                break
    
    if not current_booking:
        print(f"--- Бронирование с ID {booking_id} не найдено для страницы подтверждения. ---")
        # Можно перенаправить на страницу со списком всех бронирований или на главную
        return redirect(url_for('home')) 

    return render_template('booking_confirmation.html', title="Заявка принята", booking=current_booking)

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == '__main__':
    # Создаем пустой bookings.json, если его нет, чтобы избежать ошибок при первой загрузке
    if not os.path.exists(BOOKINGS_JSON_FILE_PATH):
        with open(BOOKINGS_JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print(f"--- Создан пустой файл {BOOKINGS_JSON_FILE_PATH} ---")
    
    app.run(debug=True, port=5000)