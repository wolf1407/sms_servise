from flask import Flask, request, jsonify , render_template
import sqlite3, datetime, os, sys

app = Flask(__name__)
executable_path = sys.executable

# Получаем путь к главной папке проекта
project_folder = os.path.dirname(os.path.abspath(executable_path))

print(project_folder)
def get_database_path(filename):
    return os.path.join(project_folder, filename)



# Маршрут для обробки запиту
@app.route('/stubs/handler_api.php', methods=['GET'])
def get_number():
    api_key = request.args.get('api_key')
    if api_key != 'admin':
        return jsonify({'error': 'Invalid API key'})
    action = request.args.get('action')

    if action == "getNumber":
        country = request.args.get('country')
        try:
            database_path = get_database_path('numbers.db')
            conn = sqlite3.connect(database_path) 
            cursor = conn.cursor()
            query = f"SELECT number, id FROM numbers WHERE status IS NULL AND country = {country} LIMIT 1"

            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                number = result[0]
                id = result[1]

                update_query = "UPDATE numbers SET status = 'wait' WHERE id = ?"
                cursor.execute(update_query, (id,))
                conn.commit()

                current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_query = "INSERT INTO tasks ( datecreate, number, status, datefinish) VALUES (?, ?, ?, ?)"
                cursor.execute(insert_query, ( current_datetime, number, 'wait', None))
                conn.commit()
                new_id = cursor.lastrowid
                writelog(f"Запит номера id {new_id}")
                return  f"ACCESS_NUMBER:{new_id}:{number}"

            else:
                return "NO_NUMBERS"

        except sqlite3.Error as error:
            return jsonify({'error': str(error)})

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif action == "getStatus":
        id = request.args.get('id')
        try:
            database_path = get_database_path('numbers.db')
            conn = sqlite3.connect(database_path) 
            cursor = conn.cursor()
            query = f"SELECT code, number, status FROM tasks WHERE id = {int(id)}"

            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                code = result[0]
                status = result[2]
                if code:
                    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    update_query = f"UPDATE tasks SET status = 'OK', datefinish = '{current_datetime}' WHERE id = ?"
                    cursor.execute(update_query, (id,))
                    

                    number = result[1]
                    update_query = f"UPDATE numbers SET status = 'Success' WHERE number = ?"
                    cursor.execute(update_query, (number,))
                    conn.commit()
                    writelog(f"Отримано код ({code}) id {id}")
                    return f'STATUS_OK:{code}'

                elif status == "wait":
                    return 'STATUS_WAIT_CODE'    

                else:
                    return 'STATUS_CANCEL'                
            else:
                writelog(f"Номерів не знайдено ")

                return 'NO_NUMBERS'

        except sqlite3.Error as error:
            return jsonify({'error': str(error)})

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif action == "setStatus":
        id = int(request.args.get('id'))
        statusid = int(request.args.get('status'))

        textreturn = ""
        status = ""
        if statusid == 8:
            writelog(f"Номер в бані ід {id}")
            status = "banned"
            textreturn = "ACCESS_CANCEL"
        elif statusid == 1:
            status = "wait"
            textreturn = "ACCESS_READY"
        elif statusid == 6:
            writelog(f"Номер в успішно завершений ід {id}")
            status = "success"
            textreturn = "ACCESS_ACTIVATION"



        

        try:
            database_path = get_database_path('numbers.db')
            conn = sqlite3.connect(database_path) 
            cursor = conn.cursor()
            update_query = f"UPDATE tasks SET status = {status} WHERE id = ?"
            cursor.execute(update_query, (id,))
            conn.commit()

            return textreturn


        except sqlite3.Error as error:
            return str(error)

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        
@app.route('/')
def index():
    try:
        database_path = get_database_path('numbers.db')
        conn = sqlite3.connect(database_path) 
        cursor = conn.cursor()

        # Вибірка активних номерів зі статусом "wait"
        select_query = "SELECT id ,number, dateCreate, code FROM tasks WHERE status = 'wait'"
        cursor.execute(select_query)
        numbers = cursor.fetchall()

        return render_template('index.html', numbers=numbers)

    except sqlite3.Error as error:
        return str(error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/all')
def all():
    try:
        database_path = get_database_path('numbers.db')
        conn = sqlite3.connect(database_path) 
        cursor = conn.cursor()

        # Вибірка активних номерів зі статусом "wait"
        select_query = "SELECT id ,number, dateCreate, status FROM tasks "
        cursor.execute(select_query)
        numbers = cursor.fetchall()

        return render_template('all.html', numbers=numbers)

    except sqlite3.Error as error:
        return str(error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@app.route('/cancel', methods=['POST'])
def cancel():
    data = request.get_json()
    try:
        id = int(data.get('id'))
        database_path = get_database_path('numbers.db')
        conn = sqlite3.connect(database_path) 
        cursor = conn.cursor()

        # Оновлення поля "status" для вказаного номера
        update_query = "UPDATE tasks SET status = 'cancel' WHERE id = ?"
        cursor.execute(update_query, (id,))
        conn.commit()
        writelog(f"Відміна номер через веб інтерфейс, ід {id}")

        return 'Номер відмінений!'


    except sqlite3.Error as error:
        return str(error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Маршрут для збереження коду
@app.route('/save', methods=['POST'])
def save_code():
    data = request.get_json()
    try:

        id = int( data.get('id'))
        code = int(data.get('code'))

        database_path = get_database_path('numbers.db')
        conn = sqlite3.connect(database_path) 
        cursor = conn.cursor()

        # Оновлення поля "code" для вказаного номера
        update_query = "UPDATE tasks SET code = ? , status = 'ready' WHERE id = ?"
        cursor.execute(update_query, (code, id))
        conn.commit()

        writelog(f"Додали код через вебінтерфейс, ід {id}")
        return 'Код успішно збережено!'

    except sqlite3.Error as error:
        return str(error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_number', methods=['GET', 'POST'])
def add_number():
    if request.method == 'POST':
        numbers = request.form.get('numbers')

        if numbers:
            numbers_list = numbers.split('\n')
            for numberx in numbers_list:
                number = numberx.strip()
                countryname = get_country_by_number(number)
                country = get_countryid_by_number(countryname)
                save_number(number,country)
                writelog(f"Додали новий {number} ({country}) номер через вебінтерфейс, ід {country}")
            return 'Номери були додані.'
        return 'Помилка: введіть номери.'
    
    return render_template('add_number.html')

def save_number(number,country):
    try:
        database_path = get_database_path('numbers.db')
        conn = sqlite3.connect(database_path) 
        cursor = conn.cursor()
        insert_query = "INSERT INTO numbers (number, country) VALUES (?,?)"
        cursor.execute(insert_query, (number,country,))
        conn.commit()

        return True
    except Exception as e:
        print(f"Помилка при збереженні номера: {e}")
        return False

def get_country_by_number(number):
    with open('code.txt', 'r', encoding="utf-8") as file:
        codes = file.readlines()
        
        for code in codes:
            country, code_digits, code = code.strip().split(':')
            code_length = len(code)
            
            if number[:code_length] == code:
                return country
        
        return "Unknown"

def get_countryid_by_number(countryname):
    with open('SMS_country_id.txt', 'r', encoding="utf-8") as file:
        codes = file.readlines()
        
        for code in codes:
            id, country= code.strip().split(':')
            if countryname.lower() == country:
                return int(id)
        
        return "Unknown"


def writelog(text):
    with open('log.txt', 'a', encoding="utf-8") as file:
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(current_datetime + " " + text + "\n")
        print(current_datetime + text)
        


if __name__ == '__main__':
    app.run()
