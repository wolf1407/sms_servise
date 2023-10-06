from flask import Flask, request
import  os, sys , requests

app = Flask(__name__)
executable_path = sys.executable

# Получаем путь к главной папке проекта
project_folder = os.path.dirname(os.path.abspath(executable_path))
#project_folder = "C:\Python\SmsService"

print(project_folder)
def get_database_path(filename):
    return os.path.join(project_folder, filename)



# Маршрут для обробки запиту
@app.route('/stubs/handler_api.php', methods=['GET'])
def get_number():
    api_key = request.args.get('api_key')
        # відкрийте файл та прочитайте ключ
    action = request.args.get('action')


    
    if action == "getNumber":
        dd = {"fb":7, "tg":19,"lf":29,"oi":33,"ig":36,"wb":43,"wa":45,"tw":49,"tn":141,"wx":154,"ds":200,"go":16,"vi":423,"vk":425}
        service = request.args.get('service')
        sv = dd[service]


        url = "https://ironsim.com/api/phone/new-session"
        params = {
            "token": api_key,
            "service": sv
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            # Опрацьовуйте дані тут
            print(data)

            number = data["data"]["phone_number"]
            id = data["data"]["session"]
            return  f"ACCESS_NUMBER:{id}:{number}"	

            
        else:
            return "BAD_ACTION"


        #https://ironsim.com/api/phone/new-session?token=ply8j2t9k5eo2wicdiknkz8852f2phcp&service=1



    elif action == "getStatus":
        id = request.args.get('id')
        url = f"https://ironsim.com/api/session/{id}/get-otp"

        params = {
            "token": api_key
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            # Опрацьовуйте дані тут
            print(data)

            if "messages" in data["data"]:
           
                code = data["data"]["messages"][0]["otp"]

                if code:
                    return  f"STATUS_OK:{code}"
                else:
                    return "STATUS_WAIT_CODE"
            else:
                return "STATUS_WAIT_CODE"
                
        else:
            return "STATUS_WAIT_CODE"

    elif action == "setStatus":
        id = request.args.get('id')
        statusid = int(request.args.get('status'))

        textreturn = ""
        if statusid == 8:

            id = request.args.get('id')
            url =  f"https://ironsim.com/api/session/cancel?token={api_key}&session={id}"

            params = {
                "token": api_key
            }
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                # Опрацьовуйте дані тут
                print(data)
                textreturn = "ACCESS_CANCEL"
        elif statusid == 1:
            textreturn = "ACCESS_READY"
        elif statusid == 6:
            textreturn = "ACCESS_ACTIVATION"
       
       
        return textreturn


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
