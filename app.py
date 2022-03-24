from flask import Flask, render_template, url_for, request, flash, redirect, session
import psycopg2
from config import host, user, password, db_name

app = Flask(__name__)
app.config['SECRET_KEY'] = '5ad30edaf0cbc613384f451979c18d6573058515a2ab'#Секретный ключ для формировании засекреченной сессии
admin_list = ['denis666']  # Список главных работников. Даннные работники имеют больше привелегий, нежели просто работники.
shops_list = [] #Небольшое хранение кэша для магазинов
employers_list = [] #Небольшое хранение кэша для магазинов
"""Файл app.py, главный файл веб-приложения"""
#Главная страница
@app.route('/')
def index():
    return render_template("index.html", shops=shops_list, employers=employers_list)


# Каталог товаров и услуг
@app.route('/catalog')
def catalog():
    if not 'logged_in' in session: #Проверка наличии сесси, для того, чтобы отобразить привествие пользователя, если он авторизован
        sess = 0
    else:
        sess = session['logged_in']
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT *
                    FROM "Item"
                """
            )
            items = cursor.fetchall()
            cursor.execute(
                f"""SELECT *
                    FROM "Service"
                """
            )
            services = cursor.fetchall()
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close() #закрытие подключения
            print("[INFO] PostgreSQL connection closed")
    return render_template("catalog.html", items=items, sess=sess, service=services)
#Передача предметов, услуг и наличии сессии для отображения в catalog.html

# Панель для добавления услуги, которую может выполнить работник
@app.route('/panel/add_service', methods=['GET', 'POST'])
def add_service():
    if 'employee' in session: #Если есть сессия работника
        typeofsession = 'service' #Тип сессии для передачи в шаблон
        try:#Коннект с БД
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                        FROM "Employee"
                        WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )#Запрос на соответствие логина и пароля
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'service_admin' #Если работник является главным, то его сессия администратора
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Если метод равен пост и тип сессии админ, он может добавлять услуги в каталог
        if request.method == "POST" and typeofsession == 'service_admin':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                                                    FROM "Employee"
                                                                    WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                                            """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass
                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Service" (name, price) VALUES ('{str(request.form['service_name'])}','{str(request.form['price'])}');
                    """
                        )
                        connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
#Если сессия не администраторская, то работник может себе добавить услугу, которую он может выполнить. Она будет одобрена, после проверки администратором.
        if request.method == "POST" and typeofsession != 'service_admin':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                            FROM "Employee"
                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                                            """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass
                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Service_Employee" ("service", "Employee") VALUES ({str(request.form['service_id'])},'{session['employee'][0]}');
                    """
                        )#Добавление услуги работнику
                        connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")

        return render_template('add_order.html', tip=typeofsession)
    return ('404')

#Обновление данных для кэша работников и магазинов на главной странице, чтобы не делать несколько раз запросов.
@app.route('/panel/refreshing', methods=['GET', 'POST'])
def refreshing():
    if request.method == 'POST':
        if 'employee' in session:
            typeofsession = 'not_admin'
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                                       FROM "Employee"
                                                       WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                               """
                    )
                    try:
                        result = cursor.fetchall()
                        if admin_list.count(result[0][0]):
                            typeofsession = 'refreshing'
                    except:
                        pass
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
            #Если сессия администратора подтверждена
            if typeofsession == 'refreshing':
                try:
                    connection = psycopg2.connect(
                        host=host,
                        user=user,
                        password=password,
                        database=db_name
                    )
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f"""SELECT "name", "telephone"
                                FROM "Employee";
                        """
                        )
                        try:
                            global employers_list#Заполнение кэша
                            employers_list = cursor.fetchall()
                            cursor.execute(
                                f"""SELECT "adress", "id_shop"
                                    FROM "Shop";
                            """
                            )
                            global shops_list
                            shops_list = cursor.fetchall()
                        except:
                            pass

                except Exception as _ex:
                    print("[INFO] Error while working with PostgreSQL", _ex)
                finally:
                    if connection:
                        connection.close()
                        print("[INFO] PostgreSQL connection closed")
        return redirect('/')
    else:
        return ('404')


# Обновление базы данных услуг, которые работник добавил и которые ждут коммита главного администратора.
@app.route('/panel/refresh', methods=['GET', 'POST'])
def refresh():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                       FROM "Employee"
                       WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'refresh'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Происходит обновление базы данных, добавление новых записей в service_shop
        if request.method == "POST" and typeofsession == 'refresh':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass

                    if result:
                        cursor.execute(
                            f"""DELETE
                                                FROM "Service_Shop"
                        """
                        )
                        connection.commit()
                        cursor.execute(
                            f"""SELECT DISTINCT service, shop
                                FROM "Shop_Employee" CROSS JOIN "Service_Employee"
                                WHERE "employee" = "Employee"
                                EXCEPT
                                SELECT "service", "shop"
                                FROM "Service_Shop"

                    """
                        )
                        updating = cursor.fetchall()
                        print(updating)
                        for i in updating:
                            cursor.execute(
                                f"""INSERT INTO "Service_Shop" ("shop", "service") VALUES ({int(i[1])}, {int(i[0])});
                            """
                            )
                            connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)
    else:
        return ('404')


# Добавление существующих сотрудников в магазины
@app.route('/panel/add_employers', methods=['GET', 'POST'])
def add_employers():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'add_employers'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")

        if request.method == "POST" and typeofsession == 'add_employers':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass

                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Shop_Employee" ("shop", "employee") VALUES ({request.form['id_shop']},'{str(request.form['employee'])}');
                    """
                        )#Добавление существующих сотрудников в магазин.
                        connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)
    else:
        return ('404')


# Добавление магазинов, адресов
@app.route('/panel/add_shop', methods=['GET', 'POST'])
def add_shop():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'add_shop'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Если сессия администратора подтверждена
        if request.method == "POST" and typeofsession == 'add_shop':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass

                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Shop" (adress) VALUES ('{str(request.form['address'])}');
                    """
                        )#Запись в таблицу Shop адресса, а id поставится автоматически.
                    connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)#Использование add_order.html
    else:
        return ('404')


# Изменение количества продукции в магазинах
@app.route('/panel/edit_item_shops', methods=['GET', 'POST'])
def edit_item_shops():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'edit_item_shops' #Подтверждение сессии Администратора
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Если сессия администратора, то
        if request.method == "POST" and typeofsession == 'edit_item_shops':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )#Доп проверка логина и пароля в сессии employee.
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass

                    if result: #Если успешно, то происходит изменение значения количества.
                        cursor.execute(
                            f"""UPDATE "Shop_Item"
                                SET "quantity" = {request.form['quantity']}
                                WHERE "shop" = {int(request.form['shop'])} AND "item" = {int(request.form['item_name'])};
                    """
                        )
                        connection.commit()
                        return ('Товар изменен')#Возвращает результат действия
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return ('Товар не изменен')
    else:
        return ('404')


# Добавление товаров в магазины...
@app.route('/panel/add_item_shops', methods=['GET', 'POST'])
def add_item_shops():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()
                    if admin_list.count(result[0][0]):
                        typeofsession = 'item_admin_shops'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Если сессия администратора подтверждена
        if request.method == "POST" and typeofsession == 'item_admin_shops':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()
                    except:
                        pass

                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Shop_Item" (shop, item, quantity) VALUES ('{str(request.form['shop'])}', {str(request.form['item_name'])}, {str(request.form['quantity'])});
                    """
                        )#Он может добавлять товар в магазин с указанием количества.
                    connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)
    else:
        return ('404')


# Панель для добавления товара в каталог главным работникам
@app.route('/panel/add_item', methods=['GET', 'POST'])
def add_item():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()

                    if admin_list.count(result[0][0]):
                        typeofsession = 'item_admin'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")

        if request.method == "POST" and typeofsession == 'item_admin':

            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()

                    except:
                        pass

                    if result:
                        cursor.execute(
                            f"""INSERT INTO "Item" (name, price) VALUES ('{str(request.form['item_name'])}', {str(request.form['price'])});
                    """
                        )#Добавление нового предмета, указание цены и названия.
                    connection.commit()#Подтверждение транзакции
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)
    else:
        return ('404')




# Панель для изменения товаров главным работником
@app.route('/panel/edit_item', methods=['GET', 'POST'])
def edit_item():
    if 'employee' in session:
        typeofsession = 'not_admin'
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                                   FROM "Employee"
                                                   WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                           """
                )
                try:
                    result = cursor.fetchall()

                    if admin_list.count(result[0][0]):
                        typeofsession = 'edit_item'
                except:
                    pass
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
#Если сессия администратора, то
        if request.method == "POST" and typeofsession == 'edit_item':

            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                    )
                    try:
                        result = cursor.fetchall()

                    except:
                        pass

                    if result:#Если авторизация прошла успешно, и нужно поменять количество, то для этого указываются 3 колонки, id предмета, магазина и количество
                        if request.form['item_name'] and request.form['shop'] and request.form['quantity']:
                            cursor.execute(
                                f"""UPDATE "Shop_Item" 
                                    SET "quantity" = {request.form['quantity']}
                                    WHERE "item" = {request.form['item_name']} AND "shop" = {request.form['shop']};
                                """
                            )
                            connection.commit()
                        #ЗЕсли нужно поменять цену, то для этого в форме нужно указать, id предмета, цену и не должно быть указано количество
                        if request.form['item_name'] and request.form['price'] and not request.form['quantity']:
                            cursor.execute(
                                f"""UPDATE "Item" 
                                    SET "price" = {request.form['price']}
                                    WHERE "id_item" = {request.form['item_name']};
                                """
                            )
                            connection.commit()
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip=typeofsession)
    else:
        return ('404')

#Функция и адрес для удаления странички пользователя.
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':#Если пользователь нажал на кнопку удалить
        if 'logged_in' in session:
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Client"
                                            WHERE login = '{str(session['logged_in'][0])}'
                    """
                    )
                    result = cursor.fetchall()
                    if not result:
                        error = 'Invalid username'
                    else:
                        if result[0][1] == session['logged_in'][1]:
                            cursor.execute(
                                f"""DELETE
                                FROM "Client"
                                WHERE "login" = '{session['logged_in'][0]}';
                                                """
                            )#Удаление клиента по логину, а так же обнуление сессии
                            connection.commit()
                            session['logged_in'] = []
                            return redirect(url_for("login"))
                        else:
                            error = 'Invalid password'
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return ('неправильно работаем')
    else:
        return ('404')

#Функция для изменения данных об пользователе
@app.route('/change', methods=['GET', 'POST'])
def change():
    if request.method == 'POST':
        if 'logged_in' in session:
            print('Чувак зареган')
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                            FROM "Client"
                                            WHERE login = '{str(session['logged_in'][0])}'
                    """
                    )
                    result = cursor.fetchall()
                    if not result:
                        error = 'Invalid username'
                    else:
                        if result[0][1] == session['logged_in'][1]:
                            print(request.form['login'])
                            print(request.form['fio'])
                            print(request.form['telephone'])
                            print(request.form['password'])
                            cursor.execute(
                                f"""UPDATE "Client"
                                    SET "fio" = '{str(request.form['fio'])}', "login" = '{str(request.form['login'])}', "password" = '{str(request.form['password'])}', "telephone" = {int(request.form['telephone'])}
                                    WHERE "login" = '{session['logged_in'][0]}';
                                                """
                            )#Получаются запросы для изменения данных
                            connection.commit()
                            return redirect(url_for("login"))
                        else:
                            error = 'Invalid password'
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return ('Не авторизован')
    else:
        return ('404')

#Функция для пополнения баланса
@app.route('/balance', methods=['GET', 'POST'])
def balance():
    if 'logged_in' in session:
        if request.method == 'POST':
            try:
                connection = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""SELECT login, password
                                FROM "Client"
                                WHERE login = '{session['logged_in'][0]}'
        """
                    )
                    result = cursor.fetchall()
                    if not result:
                        error = 'Invalid username'
                    else:#Если пароли сессии совпадают с БД
                        if str(session['logged_in'][1]) == result[0][1]:
                            cursor.execute(
                                f"""UPDATE "Client"
                                        SET "balance" = "balance" + {int(request.form['balance'])}
                                        WHERE "login" = '{session['logged_in'][0]}'
                                """
                            )
                            connection.commit()
                            return ('Успешно пополнили')
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
                return ('Счет не пополнен')
            finally:
                if connection:
                    connection.close()
                    print("[INFO] PostgreSQL connection closed")
        return render_template("cabinet.html", tip='balance')
    else:
        return ('Вы не авторизированы')

#Личный кабинет пользователя
@app.route('/inside', methods=['GET', 'POST'])
def inside():
    if 'logged_in' in session:
        print('Чувак зареган')
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT "employee", "order", "status", "price", "telephone"
FROM "Order_Employee" NATURAL JOIN "Order" NATURAL JOIN "Employee"
WHERE "order" = "nomer" and login_zak = '{session['logged_in'][0]}' and "login" = "employee"
            """
                )
                result = cursor.fetchall()
                cursor.execute(
                    f"""SELECT concat(balance::numeric,'Р'), fio
                    FROM "Client"
                    WHERE "login" = '{session['logged_in'][0]}'
                            """
                )
                balance = cursor.fetchall()
                return render_template("cabinet.html", tip='cabinet', orders=result, balance=balance)
        except Exception as _ex:
            return redirect(url_for("logout"))#Служит для избежания лишних ошибок
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
    else:
        return ('Вы не авторизированы')


# Авторизация клиента
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                        FROM "Client"
                        WHERE login = '{str(request.form['username'])}'
"""
                )
                result = cursor.fetchall()
                if not result:
                    error = 'Invalid username'
                else:
                    if str(request.form['password']) == result[0][1]:
                        # session.init_app(app)
                        print('success')
                        session['logged_in'] = [str(request.form['username']), str(request.form['password'])]
                        flash('You were logged in')
                        return redirect(url_for(""))
                    else:
                        error = 'Invalid password'
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
    return render_template('login.html', error=error, tip='login')


#Адрес для авторизации работников
@app.route('/employee', methods=['GET', 'POST'])
def employee():
    error = None
    if request.method == 'POST':
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                        FROM "Employee"
                        WHERE login = '{str(request.form['username'])}'
"""
                )#Запрос на получения логина пароля из БД
                result = cursor.fetchall()
                if not result:
                    error = 'Invalid username'
                else:#Проверка на соответствие
                    if str(request.form['password']) == result[0][1]:
                        # session.init_app(app)
                        session['employee'] = [str(request.form['username']), str(request.form['password'])]
                        flash('Вы вошли как работник')#Всплывающее окошко
                        return redirect(url_for(""))
                    else:
                        error = 'Invalid password'
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
    return render_template('employee.html', error=error, tip='login')


#Страничка заказов
@app.route('/panel/orders/<int:id>', methods=['GET', 'POST'])
def panel_orders(id):
    services = [1]
    items = [1]
    ninja1 = []#Нужно для того, чтобы передать id заказа в шаблон
    if 'employee' in session:
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT login, password
                                            FROM "Employee"
                                            WHERE login = '{session['employee'][0]}' AND password = '{session['employee'][1]}'
                    """
                )
                try:
                    result = cursor.fetchall()

                except:
                    pass
                if result:
                    cursor.execute(
                        f"""SELECT "order", "id", "name", "price", "quantity"
FROM "Order_Service" NATURAL JOIN "Service"
WHERE "order" = {id} and "service" = "id"; 
                    """
                    )
                    services = cursor.fetchall()#Получение данных об услугах по номеру заказа
                    cursor.execute(
                        f"""SELECT "order","Order_Item"."quantity", "Order_Item"."id_item", "name", "price"
                                FROM "Order_Item" CROSS JOIN "Item"
                                WHERE "order" = {id} and "Order_Item"."id_item" = "Item"."id_item";
                        """
                    )

                    items = cursor.fetchall()#Получение данных об предметах по номеру заказа
                    cursor.execute(
                        f"""SELECT "service", "quantity"
                            FROM "Order_Service"
                            WHERE "order" = {id}""")
                    services = cursor.fetchall()
                    if request.method == 'POST':
                        cursor.execute(
                            f"""SELECT "service"
                                FROM "Order_Service"
                                WHERE "order" = {id}
                                EXCEPT
                                SELECT "service"
                                FROM "Service_Employee"
                                WHERE "Employee" = '{session['employee'][0]}'
"""
                        )
                        nothaving = cursor.fetchall()#Услуги, которые отсутствуют у работника при попытке взятии данного заказа
                        if not nothaving:#Если их нет,то работник успешно принимает заказ.
                            cursor.execute(
                                f"""UPDATE "Order_Employee" 
                                    SET "employee" = '{session['employee'][0]}'
                                    WHERE "order" = {id};
                                                    """
                            )
                            connection.commit()
                            cursor.execute(
                                f"""UPDATE "Order" 
                                    SET "status" = 2
                                    WHERE "nomer" = {id};
                                                    """
                            )
                            connection.commit()
                        else:
                            return f'У тебя нет таких заказов id {nothaving}'
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
        return render_template("add_order.html", tip='order', service=services, item=items, ninja=id)
    else:
        return ('404')


# Панель работника
@app.route('/panel', methods=['GET', 'POST'])
def panel():
    if 'employee' in session:
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT "employee", "order", "status", "login_zak", "price", "telephone"
FROM "Order_Employee" NATURAL JOIN "Order" NATURAL JOIN "Client"
WHERE "employee" = '{session['employee'][0]}' AND "order" = "nomer" AND "login_zak" = "login"
                """
                )
                list_orders = cursor.fetchall()#Список взятых заказов работником
                cursor.execute(
                    f"""SELECT "employee","nomer" ,"login_zak"
                        FROM "Order" NATURAL JOIN "Order_Employee"
                        WHERE "nomer" = "order" AND "employee" = 'temp'
            """
                )
                result = cursor.fetchall()#Заказы, которые никто не принял, temp в данном случае является невалидным работником, который служит просто для оформления заказа

                # cursor.execute(
                #     f"""SELECT *
                #         FROM "Order_Service" NATURAL JOIN "Order" NATURAL JOIN "Service"
                #         WHERE login_zak = '{session['emplyoee'][0]}' AND nomer = "order"
                # """
                # )
                # result2 = cursor.fetchall()
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
        return render_template("employee.html", tip='panel', orders=result, orders2=list_orders)#Передача в employee.html
    else:
        return ('404')


# Регистрация клиента
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        print('connection')
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with connection.cursor() as cursor:
                if request.form['fio'] and request.form['login'] and request.form['password']:
                    cursor.execute(
                        f"""INSERT INTO "Client" VALUES ('{str(request.form['fio'])}', '{str(request.form['login'])}', '{str(request.form['password'])}', DEFAULT, NULL);
                        """#Добавление в БД данных о зарегестрировавшемся пользователе
                    )
                    connection.commit()
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                connection.close()
                print("[INFO] PostgreSQL connection closed")
    return render_template('login.html', error=error, tip='register')


# Страничка товара
@app.route('/item/<int:id>', methods=['GET', 'POST'])
def item(id):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT *
                    FROM "Item"
                    WHERE id_item = {id}
               """
            )
            result = cursor.fetchall()#Данные об предмете по id
            cursor.execute(
                f"""SELECT adress, quantity, shop
                    FROM "Shop_Item" CROSS JOIN "Shop"
                    WHERE "item" = {id} AND "shop" = "id_shop"
               """
            )
            havingintheshops = cursor.fetchall()#Наличие товара в магазине

    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")
    if request.method == 'POST':#Если пользователь нажал на кнопку добавить
        if 'basket' not in session:  # Создаем сессию для корзины
            session['basket'] = []
        if 'basket' in session:
            try:
                if int(request.form['quantity']):
                    session['basket'] += [{'tip': 'item',
                                           'id': id,
                                           'quantity': request.form['quantity'],
                                           'price': result[0][2],
                                           'shop': request.form['id_shop']}]#Заполнение корзины товаром
            except:
                return "Очистите корзину"

    return render_template('shop.html', id=id, item=result, tip='item', shops=havingintheshops)


# Страничка услуги
@app.route('/service/<int:id>', methods=['GET', 'POST'])
def service(id):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT *
                    FROM "Service"
                    WHERE id = {id}
               """
            )
            result = cursor.fetchall()#Информация об услугах
            cursor.execute(
                f"""SELECT adress, shop
                    FROM "Service_Shop" CROSS JOIN "Service" CROSS JOIN "Shop"
                    WHERE "service" = "id" and "service" = {id} and "shop" = "id_shop"
               """
            )
            havingintheshops = cursor.fetchall()#Наличие их в магазине

    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()
            print("[INFO] PostgreSQL connection closed")
    if request.method == 'POST':
        if 'basket' not in session:  # Создаем сессию для корзины
            session['basket'] = []
        if 'basket' in session:
            if request.form['quantity'] and request.form['id_shop'] and request.form['quantity'].isnumeric() and \
                    request.form['id_shop'].isnumeric():
                try:#Добавление в корзину услугу
                    session['basket'] += [{'tip': 'service',
                                           'id': id,
                                           'quantity': request.form['quantity'],
                                           'price': result[0][2],
                                           'shop': request.form['id_shop']}]
                except:
                    return 'Очистите корзину'
    return render_template('shop.html', id=id, item=result, tip='service', shops=havingintheshops)


# Оплата, корзина
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'logged_in' in session and session['basket']:#Сперва происходит наличие сессий корзины и авторизации.
        if 'basket' in session:
            items = session['basket']#Объявление в переменной всех предметов и услуг в корзине.
            sum = 0#Суммарная цена
            for i in session['basket']:
                if 'price' in i:
                    sum = sum + (int(i['price']) * int(i['quantity']))#Считается сумма заказа
            if request.method == "POST":
                try:
                    connection = psycopg2.connect(
                        host=host,
                        user=user,
                        password=password,
                        database=db_name
                    )
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f"""SELECT *
                                FROM "Shop_Item"
                        """
                        )
                        check1 = cursor.fetchall()
                        for i in session['basket']:#Проверка на наличие товара в магазине
                            if i['tip'] == 'item':
                                for j in check1:
                                    if 'id' and 'quantity' and 'shop' in i:
                                        if int(i['quantity']) > j[2] and int(i['id']) == j[1] and int(i['shop']) == j[0]:
                                            return ('Товара нет в магазине, в котором вы выбрали купить')
                                    else:
                                        session['basket'] = []
                                        return ('Нерпавильно заполненна корзина...')
                        cursor.execute(
                            f"""SELECT login, password, balance
                                        FROM "Client"
                                        WHERE login = '{session['logged_in'][0]}' AND password = '{session['logged_in'][1]}'
                        """
                        )
                        try:
                            result = cursor.fetchall()
                        except:
                            pass
                        if result and result[0][2] >= sum: #Проверка на соответствие логина и пароля в БД, а так же проверка баланса, он должен быть больше sum
                            cursor.execute(
                                f"""UPDATE "Client" 
                                    SET balance = balance - {sum}
                                    WHERE login = '{result[0][0]}';
                            """
                            )#Вычитание баланса
                            cursor.execute(
                                f"""INSERT INTO "Order" (status, price, login_zak) VALUES (1, {sum}, '{result[0][0]}');
                        """
                            )
                           #Добавление заказа
                            cursor.execute(
                                f"""SELECT nomer
                                FROM "Order"
                                WHERE login_zak = '{result[0][0]}'
                                ORDER BY nomer DESC
                                LIMIT 1
                            """
                            )
                            nomer = cursor.fetchone()#Номер заказа
                            cursor.execute(
                                f"""INSERT INTO "Order_Employee" (employee, "order") VALUES ('temp', {nomer[0]});
                            """
                            )

                            #Добавление к заказу временного работника, который является невалидным
                            for i in session['basket']:
                                if i['tip'] == 'item':
                                    if 'id' and 'quantity' and 'shop' in i:
                                        cursor.execute(
                                            f"""UPDATE "Shop_Item" 
                                                SET quantity = quantity - {i['quantity']} 
                                                WHERE "shop" = '{i['shop']}' and "item" = '{i['id']}';
                                        """
                                        )#Вычитание предметов, которые были куплены
                                        cursor.execute(
                                            f"""INSERT INTO "Order_Item" (id_item, "order" , quantity, shop) VALUES ({i['id']}, {nomer[0]}, {int(i['quantity'])}, {i['shop']});
                                        """
                                        )#Добавление в заказ предметов
                                if i['tip'] == 'service':
                                    if 'id' and 'quantity' and 'shop' in i:
                                        cursor.execute(
                                            f"""INSERT INTO "Order_Service" ("service", "order", "quantity", "shop") VALUES ( {i['id']}, {nomer[0]}, {int(i['quantity'])}, {i['shop']});
                                        """
                                        )#Добавление в заказ услуг

                            connection.commit()
                            session['basket'] = [] #Очищение корзины
                        else:
                            return ('Недостаточно средств')
                except Exception as _ex:
                    print("[INFO] Error while working with PostgreSQL", _ex)
                finally:
                    if connection:
                        connection.close()
                        print("[INFO] PostgreSQL connection closed")
            return render_template('shop.html', tip='checkout', items=items)
    else:
        return ('Корзина пуста')

#Функция для очищения корзины
@app.route('/clean', methods=['GET', 'POST'])
def clean():
    session['basket'] = []
    return redirect(url_for('checkout'))


# Разлогиниться
@app.route('/logout')
def logout():
    # session.pop('logged_in', None)
    if 'logged_in' in session:
        session.pop('logged_in', None)#Удаление сессии клиента
    if 'employee' in session:
        session.pop('employee', None)#Удаление сессии работника
    if 'basket' in session:
        session.pop('employee', None)#очистка корзины
    flash('You were logged out')#Всплывающее окошко, что вышел
    return redirect(url_for('index'))


if __name__ == "__main__":#Режим отладки
    app.run(debug=True)
